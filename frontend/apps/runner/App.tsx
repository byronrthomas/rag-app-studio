import { useState, useEffect, useContext } from 'react';
import { buildUrl, jsonRequest } from '@common/api';
import '@common/styles.css';
import { ChatMessage, Content, ContextRecord, empty_content } from '@common/types';
import { SingleQueryForm } from '@common/components/SingleQueryForm';
import { ChatForm } from '@common/components/chatbot/ChatForm';
import { H1, H2, H4 } from '@common/components/Headers';
import { Tab } from '@mui/base/Tab';
import { TabsList } from '@mui/base/TabsList';
import { TabPanel } from '@mui/base/TabPanel';
import { Tabs } from '@mui/base/Tabs';
import { ContentBlockDiv, LightBorderedDiv } from '@common/components/Divs';
import { KnowledgeBasePanel } from '@common/components/KnowledgeBasePanel';
import { IsLoadingContext } from '@common/components/IsLoadingContext';
import { LoadingOverlayProvider } from '@common/components/LoadingOverlayProvider';
import { TextArea } from '@common/components/TextArea';

const newOpenAIAPIRequest = () => { return { "model": "rag_model" }; }
type openAICompletionResponseWithContexts = {
  "id": string,
  "object": string,
  "created": number,
  "model": string,
  "system_fingerprint": string,
  "choices": {
    "text": string,
    "index": number,
    "finish_reason": "length",
    "contexts": ContextRecord[]
  }[],
  "usage": {
    "prompt_tokens": -1,
    "completion_tokens": -1,
    "total_tokens": -1,
  },
};

type openAIChatResponseWithContexts = {
  "id": string,
  "object": string,
  "created": number,
  "model": string,
  "choices": {
    "message": ChatMessage,
    "index": number,
    "finish_reason": "length",
    "contexts": ContextRecord[]
  }[],
  "usage": {
    "prompt_tokens": -1,
    "completion_tokens": -1,
    "total_tokens": -1,
  },
};

const App = () => {
  const [content, setContent] = useState<Content>(empty_content);

  useEffect(() => {
    // Fetch initial data from the server to populate the state
    fetch(buildUrl('/api/data'))  // Assume this endpoint provides the necessary data
      .then(response => response.json())
      .then(data => {
        setContent(data);
        window.document.title = `${data.app_name} - Rag App Studio`;
      })
      .catch(error => console.error('Error fetching initial data:', error));
  }, []);

  return (
    <LoadingOverlayProvider>
      <AppNamePanel content={content} />
      <UseLLMBlock />
      <ContentBlockDiv extraClasses={["m-4 flex flex-row space-x-8"]}>

        <KnowledgeBasePanel content={content} />
        <LLM content={content} />
      </ContentBlockDiv>
    </LoadingOverlayProvider>
  );
};

const AppNamePanel = ({ content }: {
  content: Content
}) => {

  return (
    <ContentBlockDiv extraClasses={["m-4"]}>
      <LightBorderedDiv>
        <div style={{ display: "flex", flexDirection: "row", justifyContent: "space-between" }}>
          <H1 extraClasses={["text-red"]} text={`RAG Application: ${content.app_name}`} />
          <div style={{ display: "flex", flexDirection: "column", alignSelf: "center" }}>
            <img style={{ height: "3em" }} alt="RAG App Studio" src="/rag_app_studio_logo.png" />
          </div>

        </div>

        <div className="flex flex-row my-2 gap-4">
          <label>Saved to Repo</label>
          <input className="w-80" type="text" value={content.repo_name} disabled />
          <label>Last app change</label>
          <input className="w-80" type="text" value={content.last_checkpoint} disabled />
        </div>

      </LightBorderedDiv>
    </ContentBlockDiv >
  );
};


const UseLLMBlock = () => {
  const [completion, setCompletion] = useState('');
  const [queryContexts, setQueryContexts] = useState<ContextRecord[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'system', content: 'You are a helpful assistant.' },
  ]);
  const [chatContexts, setChatContexts] = useState<ContextRecord[]>([]);
  const [tabIndex, setTabIndex] = useState(1);
  const setSubmitting = useContext(IsLoadingContext);

  const handleSubmitQuery = async (prompt: string) => {
    setSubmitting(true);
    const data = await jsonRequest('/v1/completions?include_contexts=1', { prompt, ...newOpenAIAPIRequest() });
    setSubmitting(false);
    const typedData = data as openAICompletionResponseWithContexts;
    setCompletion(typedData.choices[0].text);
    setQueryContexts(typedData.choices[0].contexts);
  };
  const handleSubmitChat = async (messagesToSend: ChatMessage[]) => {
    setSubmitting(true);
    const data = await jsonRequest('/v1/chat/completions?include_contexts=1', { messages: messagesToSend, ...newOpenAIAPIRequest() });
    setSubmitting(false);
    const typedData = data as openAIChatResponseWithContexts;
    setMessages([...messagesToSend, { role: 'assistant', content: typedData.choices[0].message.content }]);
    setChatContexts(typedData.choices[0].contexts);
  };

  const nonSelectedTabClasses = "border-2 p-2 bg-gray-panel-bg";
  const selectedTabClasses = "border-2 p-2 bg-gold";
  return (<div className="flex m-4">
    <div className='w-full'>

      <Tabs value={tabIndex} onChange={(_, newVal) => { setTabIndex(newVal as number) }}>
        <TabsList>
          <Tab value={1} className={tabIndex == 1 ? selectedTabClasses : nonSelectedTabClasses} style={{ borderBottomStyle: "none" }}><H2 text="Chat" /></Tab>
          <Tab value={2} className={(tabIndex == 2 ? selectedTabClasses : nonSelectedTabClasses) + " mx-2"} style={{ borderBottomStyle: "none" }}><H2 text="One-off query" /></Tab>
        </TabsList>
        <ContentBlockDiv>
          <TabPanel value={1}>
            <ChatForm prevMessages={messages} contexts={chatContexts} handleSubmitChat={handleSubmitChat} key={messages.length} />

          </TabPanel>
          <TabPanel value={2}>
            <SingleQueryForm completion={completion} contexts={queryContexts} handleSubmit={handleSubmitQuery} />
          </TabPanel>
        </ContentBlockDiv>
      </Tabs>
    </div>

  </div >
  );
}


const LLM = ({ content }: { content: Content }) => {
  return (
    <LightBorderedDiv extraClasses={["w-1/2"]}>
      <H2 text="LLM (for generation)" />
      <div>
        <div className="field-group">
          <label>Model name:</label>
          <input type="text" value={content.llm_model} disabled />
        </div>
        <QueryTemplatePanel content={content} />
        <ChatTemplatePanel content={content} />
      </div>
    </LightBorderedDiv>
  );
};

const LabelledReadonlyTextArea = ({ label, value }: { label: string, value: string }) => {
  return (<div className="flex flex-col my-2">
    <div className="flex flex-row">
      <label className="font-semibold text-blue">{label}</label>
    </div>
    <TextArea extraClasses={["bg-gray-dark/30"]} value={value} disabled />
  </div>)
}

const QueryTemplatePanel = ({ content }: { content: Content }) => {
  return (
    <div id="queryTemplateForm" className="my-4 bg-whitesmoke p-2">
      <H4 extraClasses={["underline"]} text="Query prompts" />
      <LabelledReadonlyTextArea label="Question answering:" value={content.query_prompts.text_qa_template} />
      <LabelledReadonlyTextArea label="Use more context to refine:" value={content.query_prompts.refine_template} />

    </div>
  );
}



const ChatTemplatePanel = ({ content }: { content: Content }) => {
  return (
    <div id="chatTemplateForm" className="my-4 bg-whitesmoke p-2">
      <H4 extraClasses={["underline"]} text="Chat prompts" />
      <LabelledReadonlyTextArea label="Complete next chat:" value={content.chat_prompts.context_prompt} />
      <LabelledReadonlyTextArea label="Build a question based on history & context:" value={content.chat_prompts.condense_prompt} />
    </div>
  );
}

export default App;