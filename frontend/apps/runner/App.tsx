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
import { Select, Option } from '@mui/base';
import { getUserId } from './userId';
import { ModelParamsPanel } from '@common/components/chatbot/ModelParamsPanel';
import { DEFAULT_MODEL_PARAMS, encodeForTransports as encodeForTransport, findParamIssues } from '@common/components/chatbot/ModelParams';
import { LogFooter } from '@common/components/LogDisplay';

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
      .catch(error => { console.error('Error fetching initial data:', error); alert("Something wrong - is server working correctly, failed to fetch initial data"); });
  }, []);

  return (
    <LoadingOverlayProvider>
      <AppNamePanel content={content} />
      <UseLLMBlock />
      <ContentBlockDiv extraClasses={["m-4 flex flex-row space-x-8"]}>
        <H2 text="App configuration details (for info only)" />
        <KnowledgeBasePanel content={content} />
        <LLM content={content} />
      </ContentBlockDiv>
      <LogFooter logUrl="/logs" />
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

type ChatHistories = {
  key: string,
  messages: ChatMessage[]
}[];

const chatHistoryDisplay = (chatHistoryRec: { key: string, messages: ChatMessage[] }) => {
  if (chatHistoryRec.messages.length == 0) {
    return ''
  }
  const firstUserMessage = chatHistoryRec.messages.find(m => m.role == 'user');
  if (!firstUserMessage) {
    return '';
  }
  const contentToSummarise = firstUserMessage.content;
  const messageCount = ` [${chatHistoryRec.messages.length} messages]`;
  if (contentToSummarise.length > 40) {
    return contentToSummarise.substring(0, 37) + '...' + messageCount;
  }
  return contentToSummarise + messageCount;
}

const fetchChatHistories = (userId: string) => {
  return fetch(buildUrl(`/chat-history/${userId}`), {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    }
  }).then(response => response.json())
    .then((data) => (data as ChatHistories));
}

const ChatHistoryOptions = ({ chatHistories, chatHistoryIndex, setChatHistoryIndex }: { chatHistories: ChatHistories, chatHistoryIndex: number, setChatHistoryIndex: (index: number) => void }) => {
  const commonClasses = "bg-whitesmoke border border-blue border-2 w-192";

  const popupClasses = commonClasses + " hover:cursor-pointer -z-1";
  if (chatHistories.length == 0) {
    return <Select className={commonClasses} disabled value={-1} onChange={(_, newValue) => setChatHistoryIndex(newValue as number)} slotProps={{ popup: { className: popupClasses, disablePortal: true } }}>
      <Option key={-1} value={-1}>No chat history</Option>
    </Select>
  }

  const enabledOptionClasses = "bg-whitesmoke hover:bg-blue hover:text-whitesmoke";
  return (<Select className={commonClasses} disabled={chatHistories.length == 0} value={chatHistoryIndex} onChange={(_, newValue) => setChatHistoryIndex(newValue as number)} slotProps={{ popup: { className: popupClasses, disablePortal: true } }}>

    {chatHistories.map((historyRec, i) => (
      <Option className={enabledOptionClasses} key={i} value={i}>{chatHistoryDisplay(historyRec)}</Option>
    ))}
    {chatHistoryIndex >= 0 && <Option className={enabledOptionClasses} key={-1} value={-1}>Begin a new chat..</Option>}
  </Select>);
}

type ChatInterfaceBlockProps = {
  messages: ChatMessage[],
  chatContexts: ContextRecord[],
  handleSubmitChat: (messagesToSend: ChatMessage[], modelParams: Map<string, number>) => void,
}

const ChatInterfaceBlock = ({ messages, chatContexts, handleSubmitChat }: ChatInterfaceBlockProps) => {
  const [modelParams, setModelParams] = useState(DEFAULT_MODEL_PARAMS);

  const onChatSubmitted = (messagesToSend: ChatMessage[]) => {
    const paramIssues = findParamIssues(modelParams);
    if (paramIssues.length > 0) {
      alert('Please correct the following issues with the inference settings: ' + paramIssues.join(', '));
      return;
    }
    handleSubmitChat(messagesToSend, encodeForTransport(modelParams));
  }

  return (<div className="flex flex-row gap-2">
    <div className="w-2/3">
      <ChatForm prevMessages={messages} contexts={chatContexts} handleSubmitChat={onChatSubmitted} key={messages.length} />
    </div>
    <div className="w-1/3">
      <ModelParamsPanel modelParams={modelParams} onModelParamsChange={setModelParams} />
    </div>
  </div>)
}

type QueryInterfaceBlockProps = {
  lastCompletion: string,
  queryContexts: ContextRecord[],
  handleSubmitQuery: (prompt: string, modelParams: Map<string, number>) => void,
}

const QueryInterfaceBlock = ({ lastCompletion, queryContexts, handleSubmitQuery }: QueryInterfaceBlockProps) => {
  const [modelParams, setModelParams] = useState(DEFAULT_MODEL_PARAMS);

  const onQuerySubmitted = (prompt: string) => {
    const paramIssues = findParamIssues(modelParams);
    if (paramIssues.length > 0) {
      alert('Please correct the following issues with the inference settings: ' + paramIssues.join(', '));
      return;
    }
    handleSubmitQuery(prompt, encodeForTransport(modelParams));
  }

  return (<div className="flex flex-row gap-2">
    <div className="w-2/3">
      <SingleQueryForm completion={lastCompletion} contexts={queryContexts} handleSubmit={onQuerySubmitted} />
    </div>
    <div className="w-1/3">
      <ModelParamsPanel modelParams={modelParams} onModelParamsChange={setModelParams} />
    </div>
  </div>)
}

const UseLLMBlock = () => {
  const [completion, setCompletion] = useState('');
  const [queryContexts, setQueryContexts] = useState<ContextRecord[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatContexts, setChatContexts] = useState<ContextRecord[]>([]);
  const [tabIndex, setTabIndex] = useState(1);
  const [chatHistoryIndex, setChatHistoryIndex] = useState(-1);
  const [chatHistories, setChatHistories] = useState<ChatHistories>([]);
  const [userId, setUserId] = useState('');
  const setSubmitting = useContext(IsLoadingContext);
  const onError = (_: unknown) => {
    setSubmitting(false);
  }

  useEffect(() => {
    const uid = getUserId();
    //console.log('User ID:', uid);
    setUserId(uid);
  }, []);
  useEffect(() => {
    if (userId !== '') {
      fetchChatHistories(userId).then(histories => {
        setChatHistories(histories);
      })
        .catch(error => console.error('Error:', error))
    }
  }, [userId]);


  const handleSubmitQuery = async (prompt: string) => {
    setSubmitting(true);
    const data = await jsonRequest('/v1/completions?include_contexts=1', { prompt, ...newOpenAIAPIRequest() }, onError);
    setSubmitting(false);
    const typedData = data as openAICompletionResponseWithContexts;
    setCompletion(typedData.choices[0].text);
    setQueryContexts(typedData.choices[0].contexts);
  };
  const handleSubmitChat = async (messagesToSend: ChatMessage[], modelParams: Map<string, number>) => {
    setSubmitting(true);
    const userDetails = userId !== '' ? { user: userId } : {};
    console.log("modelParams", modelParams);
    console.log({ ...modelParams.entries() })
    const reqData = { messages: messagesToSend, ...newOpenAIAPIRequest(), ...userDetails };
    for (const [key, value] of modelParams.entries()) {
      //console.log(key, value);
      // @ts-expect-error key-is-string
      reqData[key] = value;
    }
    console.log("reqData", reqData);
    const data = await jsonRequest('/v1/chat/completions?include_contexts=1', reqData, onError);
    const typedData = data as openAIChatResponseWithContexts;
    setMessages([...messagesToSend, { role: 'assistant', content: typedData.choices[0].message.content }]);
    setChatContexts(typedData.choices[0].contexts);
    if (userId !== '') {
      const updatedHistories = await fetchChatHistories(userId);
      setChatHistories(updatedHistories);
    } else {
      setChatHistories([{ key: "unknown", messages: messages }]);
    }

    setChatHistoryIndex(0);
    setSubmitting(false);
  };
  const loadChat = (index: number | null) => {
    if (index === null || index < 0) {
      setChatHistoryIndex(-1);
      setMessages([]);
      return;
    }
    setChatHistoryIndex(index);
    setMessages(chatHistories[index].messages);
  }

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
            <div className="flex flex-col">
              <div className="flex flex-row gap-2">

                <div className="w-2/3">

                  <div className="flex flex-row justify-between content-center items-center my-2">
                    <div>Extend a previous chat:</div>
                    <form>
                      <ChatHistoryOptions chatHistories={chatHistories} chatHistoryIndex={chatHistoryIndex} setChatHistoryIndex={loadChat} />
                    </form>
                  </div>





                </div>

              </div>
              <ChatInterfaceBlock messages={messages} chatContexts={chatContexts} handleSubmitChat={handleSubmitChat} />
            </div>

          </TabPanel>
          <TabPanel value={2}>
            <QueryInterfaceBlock lastCompletion={completion} queryContexts={queryContexts} handleSubmitQuery={handleSubmitQuery} />
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
      <div className="my-4 space-y-4">
        <div className="space-y-2">
          <div className="flex flex-row justify-between">
            <label>LLM model:</label>
            <input className="w-3/4" type="text" value={content.llm_model} disabled />
          </div>
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