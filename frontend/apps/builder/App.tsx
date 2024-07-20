import React, { useState, useEffect, useContext } from 'react';
import { buildUrl, jsonRequest, jsonRequestThenReload } from '@common/api';
import '@common/styles.css';
import { ChatMessage, Content, ContextRecord, empty_content } from '@common/types';
import { SingleQueryForm } from '@common/components/SingleQueryForm';
import { ChatForm } from '@common/components/chatbot/ChatForm';
import { H2, H4 } from '@common/components/Headers';
import { SubmitButton } from '@common/components/SubmitButton';
import { ContentBlockDiv, LightBorderedDiv } from '@common/components/Divs';
import { TextArea } from '@common/components/TextArea';
import { KnowledgeBasePanel } from '@common/components/KnowledgeBasePanel';
import { Select, Option } from '@mui/base';
import { Tab } from '@mui/base/Tab';
import { TabsList } from '@mui/base/TabsList';
import { TabPanel } from '@mui/base/TabPanel';
import { Tabs } from '@mui/base/Tabs';
import { IsLoadingContext } from '@common/components/IsLoadingContext';
import { LoadingOverlayProvider } from '@common/components/LoadingOverlayProvider';
import { LogFooter } from '@common/components/LogDisplay';
import { PrimaryButton } from '@common/components/PrimaryButton';
import { CHAT_CONDENSE_TEMPLATE, CHAT_QUESTION_TEMPLATE, QUERY_QA_TEMPLATE, QUERY_REFINE_TEMPLATE } from './promptTemplates';


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
      <AppNameForm content={content} />
      <ContentBlockDiv extraClasses={["m-4 flex flex-row space-x-8"]}>
        <KnowledgeBasePanel content={content} allowUpload={true} />
        <LLM content={content} />
      </ContentBlockDiv>
      <TryLLMBlock />

      <RetrievalEvaluation />
      <LogFooter logUrl="/api/logs" />
    </LoadingOverlayProvider>
  );
};

const AppNameForm = ({ content }: {
  content: Content
}) => {
  const [appName, setAppName] = useState('');
  const setSubmitting = useContext(IsLoadingContext);
  const onError = (_: unknown) => {
    setSubmitting(false);
  }

  const handleSubmit = (event: { preventDefault: () => void; }) => {
    event.preventDefault();
    setSubmitting(true);
    return jsonRequestThenReload('/api/update-app-name', { app_name: appName }, onError);
  };

  return (
    <>
      <ContentBlockDiv extraClasses={["m-4"]}>
        <LightBorderedDiv>
          <div className="flex flex-row justify-between">
            <H2 extraClasses={["text-red"]} text={`RAG Application: ${content.app_name}`} />
            <H2 extraClasses={["text-blue", "text-none"]} text="BUILD MODE" />
          </div>


          <form id="appNameForm" onSubmit={handleSubmit}>
            <div className="flex flex-row my-4 justify-between">
              <div className="flex flex-row gap-4">
                <input className="w-80" type="text" value={appName} onChange={(e) => setAppName(e.target.value)} placeholder={content.app_name} />
                <SubmitButton disabled={!appName} text="Rename" />
              </div>

              <div className="flex flex-row gap-4">
                <label>Saved to Repo</label>
                <input className="w-80" type="text" value={content.repo_name} disabled />
              </div>

              <div className="flex flex-row gap-4">
                <label>Last app change</label>
                <input className="w-80" type="text" value={content.last_checkpoint} disabled />
              </div>
            </div>
          </form>
        </LightBorderedDiv>
      </ContentBlockDiv></>
  );
};

const LLM = ({ content }: { content: Content }) => {
  const [modelName, setModelName] = useState('');
  const [selectedTab, setSelectedTab] = useState(1);
  const setSubmitting = useContext(IsLoadingContext);
  const onError = (_: unknown) => {
    setSubmitting(false);
  }
  const handleModelSubmit = (event: React.ChangeEvent<never>) => {
    if (!modelName) {
      return;
    }
    setSubmitting(true);
    event.preventDefault();
    return jsonRequestThenReload('/api/update-model', { model_name: modelName }, onError);
  };

  const supportedModels = [
    "google/gemma-2b-it", "google/gemma-7b-it",
    /* 18GB */ "google/gemma-2-9b-it",
    "mistralai/Mistral-7B-Instruct-v0.1",
    "meta-llama/Meta-Llama-3-8B-Instruct",
    "meta-llama/Llama-2-7b-chat-hf"];

  const commonTabClasses = "p-1 border border-green hover:cursor-pointer bg-whitesmoke";
  const selectedTabClasses = `${commonTabClasses} underline font-semibold`;
  const nonSelectedTabClasses = `${commonTabClasses}`;
  const tab1Classes = selectedTab === 1 ? selectedTabClasses : nonSelectedTabClasses;
  const tab2Classes = selectedTab === 2 ? selectedTabClasses : nonSelectedTabClasses;
  return (
    <LightBorderedDiv extraClasses={["w-1/2"]}>
      <H2 text="LLM (for generation)" />
      <div className="my-4 space-y-4">
        <div className="space-y-2">
          <div className="flex flex-row justify-between">
            <label>LLM model:</label>
            <input className="w-3/4" type="text" value={content.llm_model} disabled />
          </div>
          <form id="llmModelForm" onSubmit={handleModelSubmit}>
            <div className="flex flex-row justify-between content-center items-center">
              <SubmitButton disabled={!modelName} text="Change" />
              <Select className="bg-whitesmoke w-3/4 border border-blue border-2" value={modelName} onChange={(_, newValue) => setModelName(newValue!)} slotProps={{ popup: { className: 'bg-whitesmoke border border-blue border-2 w-auto' } }}>
                {supportedModels.map((model) => (
                  <Option key={model} value={model}>{model}</Option>
                ))}
              </Select>


            </div>
          </form>
        </div>
        <Tabs value={selectedTab} onChange={(_, newValue) => setSelectedTab(newValue as number)}>
          <TabsList className="space-x-2">
            <Tab className={tab1Classes} style={{ borderBottomStyle: "none" }} value={1}>Query prompts</Tab>
            <Tab className={tab2Classes} style={{ borderBottomStyle: "none" }} value={2}>Chat prompts</Tab>
          </TabsList>
          <div className="bg-whitesmoke p-2 border border-green">
            <TabPanel value={1}>
              <QueryTemplateForm content={content} />
            </TabPanel>
            <TabPanel value={2}>
              <ChatTemplateForm content={content} />
            </TabPanel>
          </div>

        </Tabs>
      </div>
    </LightBorderedDiv>
  );
};

const TextAreaFieldGroup = ({ label, currentVal, onChange, initialVal }: {
  label: string;
  currentVal: string;
  onChange: (e: string) => void;
  initialVal: string;
}) => {
  const [lastInitialVal, setLastInitialVal] = useState(initialVal);
  useEffect(() => {

    if (initialVal !== lastInitialVal) {
      // console.log('initialVal has changed - ', initialVal, lastInitialVal);

      setLastInitialVal(initialVal);
      onChange(initialVal);
    }
  }, [initialVal, lastInitialVal, onChange]);

  return (
    <div className="flex flex-col my-2">
      <div className="flex flex-row">
        <label className="font-semibold text-blue">{label}</label>
      </div>
      <TextArea value={currentVal} onChange={(e) => { onChange(e.target.value); }} />
    </div>
  );
};

const QueryTemplateForm = ({ content }: { content: Content }) => {
  const [newQaTemplate, setQATemplate] = useState(content.query_prompts.text_qa_template);
  const [refineTemplate, setRefineTemplate] = useState(content.query_prompts.refine_template);
  const setSubmitting = useContext(IsLoadingContext);
  const onError = (_: unknown) => {
    setSubmitting(false);
  }

  const handleSubmit = (event: React.ChangeEvent<never>) => {
    event.preventDefault();
    setSubmitting(true);

    return jsonRequestThenReload('/api/update-query-prompts', { text_qa_template: newQaTemplate, refine_template: refineTemplate }, onError);
  };

  const canSubmit = newQaTemplate !== content.query_prompts.text_qa_template || refineTemplate !== content.query_prompts.refine_template;
  const canReset = newQaTemplate !== QUERY_QA_TEMPLATE || refineTemplate !== QUERY_REFINE_TEMPLATE;

  return (
    <form id="queryTemplateForm" onSubmit={handleSubmit}>
      <H4 extraClasses={["underline"]} text="Query prompts" />
      <TextAreaFieldGroup label="Question answering:" currentVal={newQaTemplate} onChange={setQATemplate} initialVal={content.query_prompts.text_qa_template} />
      <TextAreaFieldGroup label="Use more context to refine:" currentVal={refineTemplate} onChange={setRefineTemplate} initialVal={content.query_prompts.refine_template} />

      <div className="flex flex-row gap-4">
        <SubmitButton text="Update query prompts" disabled={!canSubmit} />
        <PrimaryButton text="Load default query prompts" disabled={!canReset} onClick={(e) => {
          e.preventDefault();
          setQATemplate(QUERY_QA_TEMPLATE);
          setRefineTemplate(QUERY_REFINE_TEMPLATE);
        }} />
      </div>
    </form>
  );
}


const ChatTemplateForm = ({ content }: { content: Content }) => {
  const [contextPrompt, setContextPrompt] = useState(content.chat_prompts.context_prompt);
  const [condensePrompt, setCondensePrompt] = useState(content.chat_prompts.condense_prompt);
  const setSubmitting = useContext(IsLoadingContext);
  const onError = (_: unknown) => {
    setSubmitting(false);
  }

  const handleSubmit = (event: { preventDefault: () => void; }) => {
    event.preventDefault();
    setSubmitting(true);
    return jsonRequestThenReload('/api/update-chat-prompts', { context_prompt: contextPrompt, condense_prompt: condensePrompt }, onError);
  };
  const canSubmit = contextPrompt !== content.chat_prompts.context_prompt || condensePrompt !== content.chat_prompts.condense_prompt;
  const canReset = contextPrompt !== CHAT_QUESTION_TEMPLATE || condensePrompt !== CHAT_CONDENSE_TEMPLATE;

  return (
    <form id="chatTemplateForm" onSubmit={handleSubmit}>
      <H4 extraClasses={["underline"]} text="Chat prompts" />
      <TextAreaFieldGroup label="Complete next chat:" currentVal={contextPrompt} onChange={setContextPrompt} initialVal={content.chat_prompts.context_prompt} />
      <TextAreaFieldGroup label="Build a question based on history & context" currentVal={condensePrompt} onChange={setCondensePrompt} initialVal={content.chat_prompts.condense_prompt} />
      <div className="flex flex-row gap-4">
        <SubmitButton text="Update chat prompts" disabled={!canSubmit} />
        <PrimaryButton text="Load default chat prompts" disabled={!canReset} onClick={(e) => {
          e.preventDefault();
          setContextPrompt(CHAT_QUESTION_TEMPLATE);
          setCondensePrompt(CHAT_CONDENSE_TEMPLATE);
        }} />
      </div>
    </form>
  );
}

const TryLLMBlock = () => {
  const [completion, setCompletion] = useState('');
  const [queryContexts, setQueryContexts] = useState<ContextRecord[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatContexts, setChatContexts] = useState<ContextRecord[]>([]);
  const setSubmitting = useContext(IsLoadingContext);
  const onError = (_: unknown) => {
    setSubmitting(false);
  }

  const handleSubmitQuery = async (prompt: string) => {
    setSubmitting(true);
    const data = await jsonRequest('/api/try-completion', { prompt }, onError);
    setSubmitting(false);
    const typedData = data as { completion: string; contexts: ContextRecord[]; };
    setCompletion(typedData.completion);
    setQueryContexts(typedData.contexts);
  };
  const handleSubmitChat = (messagesToSend: ChatMessage[]) => {
    setSubmitting(true);
    return jsonRequest('/api/try-chat', { messages: messagesToSend }, onError)
      .then((data) => {
        setSubmitting(false);
        const typedData = data as { completion: string, contexts: ContextRecord[] };
        setMessages([...messagesToSend, { role: 'assistant', content: typedData.completion }]);
        setChatContexts(typedData.contexts);
      });
  };

  return (
    <ContentBlockDiv extraClasses={["m-4", "flex", "flex-row", "space-x-8"]}>
      <LightBorderedDiv extraClasses={["w-1/2"]}>
        <H2 text="Try a single query:" />
        <SingleQueryForm completion={completion} contexts={queryContexts} handleSubmit={handleSubmitQuery} />
      </LightBorderedDiv>
      <LightBorderedDiv extraClasses={["w-1/2"]}>
        <H2 text="Try a chat" />
        <ChatForm prevMessages={messages} contexts={chatContexts} handleSubmitChat={handleSubmitChat} key={messages.length} />
      </LightBorderedDiv>
    </ContentBlockDiv>);
}

const RetrievalEvaluation = () => {
  return (
    <div className={`border-2 p-4 m-4 bg-gray-panel-bg`}>
      <a className="text-blue" href="/evaluation/"><H4 text="Retrieval evaluation" /></a>
    </div>


  );
};



export default App;