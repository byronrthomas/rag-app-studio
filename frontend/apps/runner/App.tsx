import { useState, useEffect } from 'react';
import { buildUrl, jsonRequest } from '@common/api';
import '@common/styles.css';
import { ChatMessage, Content, ContextRecord, empty_content } from '@common/types';
import { SingleQueryForm } from '@common/components/SingleQueryForm';
import { ChatForm } from '@common/components/chatbot/ChatForm';
import { H1, H2, H3, H4 } from '@common/components/Headers';
import { Tab } from '@mui/base/Tab';
import { TabsList } from '@mui/base/TabsList';
import { TabPanel } from '@mui/base/TabPanel';
import { Tabs } from '@mui/base/Tabs';

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
    <>
      <AppNamePanel content={content} />
      <UseLLMBlock />
      <div className="content-block">

        <KnowledgeBase content={content} />
        <LLM content={content} />
      </div>
    </>
  );
};

const UseLLMBlock = () => {
  const [completion, setCompletion] = useState('');
  const [queryContexts, setQueryContexts] = useState<ContextRecord[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'system', content: 'You are a helpful assistant.' },
  ]);
  const [chatContexts, setChatContexts] = useState<ContextRecord[]>([]);

  const handleSubmitQuery = async (prompt: string) => {
    const data = await jsonRequest('/v1/completions?include_contexts=1', { prompt, ...newOpenAIAPIRequest() });
    const typedData = data as openAICompletionResponseWithContexts;
    setCompletion(typedData.choices[0].text);
    setQueryContexts(typedData.choices[0].contexts);
  };
  const handleSubmitChat = async (messagesToSend: ChatMessage[]) => {
    const data = await jsonRequest('/v1/chat/completions?include_contexts=1', { messages: messagesToSend, ...newOpenAIAPIRequest() });
    const typedData = data as openAIChatResponseWithContexts;
    setMessages([...messagesToSend, { role: 'assistant', content: typedData.choices[0].message.content }]);
    setChatContexts(typedData.choices[0].contexts);
  };

  return (<div className="flex m-4">
    <div className='w-full'>

      <Tabs defaultValue={1}>
        <TabsList>
          <Tab value={1} className="border-2 p-2 bg-gray-panel-bg" style={{ borderBottomStyle: "none" }}><H2 text="Chat" /></Tab>
          <Tab value={2} className="border-2 p-2 mx-2 bg-gray-panel-bg" style={{ borderBottomStyle: "none" }}><H2 text="One-off query" /></Tab>
        </TabsList>
        <div className="border-2 p-4 bg-gray-panel-bg">
          <TabPanel value={1}>
            <ChatForm prevMessages={messages} contexts={chatContexts} handleSubmitChat={handleSubmitChat} key={messages.length} />

          </TabPanel>
          <TabPanel value={2}>
            <SingleQueryForm completion={completion} contexts={queryContexts} handleSubmit={handleSubmitQuery} />
          </TabPanel>
        </div>
      </Tabs>
    </div>

  </div>
  );
}

const AppNamePanel = ({ content }: {
  content: Content
}) => {

  return (
    <div className="content-block">
      <div className="content-pane single-pane">
        <div style={{ display: "flex", flexDirection: "row", justifyContent: "space-between" }}>
          <H1 extraClasses={["text-red"]} text={`RAG Application: ${content.app_name}`} />
          <div style={{ display: "flex", flexDirection: "column", alignSelf: "center" }}>
            <img style={{ height: "3em" }} alt="RAG App Studio" src="/rag_app_studio_logo.png" />
          </div>

        </div>

        <H3 text={`Reading from Repo ${content.repo_name}`} />

      </div>
    </div>
  );
};

const KnowledgeBase = ({ content }: { content: Content }) => {
  return (
    <div className="content-pane">
      <H2 text="Knowledge-base (for retrieval)" />
      <div>
        <div className="field-group">
          <label>Embedding model:</label>
          <input type="text" value={content.embed_model} disabled />
        </div>
        <div>
          <label>Files uploaded:</label>
          <ul>
            {content.files && content.files.map((file, index) => (
              <li key={index}>{file}</li>
            ))}
          </ul>
        </div>
        <div className="field-group">
          <label>Latest checkpoint:</label>
          <input type="text" value={content.last_checkpoint} disabled />
        </div>
      </div>
    </div>
  );
};

const LLM = ({ content }: { content: Content }) => {
  return (
    <div className="content-pane">
      <H2 text="LLM (for generation)" />
      <div>
        <div className="field-group">
          <label>Model name:</label>
          <input type="text" value={content.llm_model} disabled />
        </div>
        <QueryTemplatePanel content={content} />
        <ChatTemplatePanel content={content} />
      </div>
    </div>
  );
};


const QueryTemplatePanel = ({ content }: { content: Content }) => {
  return (
    <div id="queryTemplateForm">
      <H4 text="Query prompts" />
      <div className="field-group">
        <label>Question answering:</label>
        <textarea value={content.query_prompts.text_qa_template} disabled />
      </div>
      <div className="field-group">
        <label>Refine template:</label>
        <textarea value={content.query_prompts.refine_template} disabled />
      </div>
    </div>
  );
}



const ChatTemplatePanel = ({ content }: { content: Content }) => {
  return (
    <div id="chatTemplateForm">
      <H4 text="Chat prompts" />
      <div className="field-group">
        <label>Complete next chat:</label>
        <textarea value={content.chat_prompts.context_prompt} disabled />
      </div>
      <div className="field-group">
        <label>Build a question based on history & context:</label>
        <textarea value={content.chat_prompts.condense_prompt} disabled />
      </div>
    </div>
  );
}

export default App;