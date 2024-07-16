import React, { useState, useEffect } from 'react';
import { buildUrl, jsonRequest, jsonRequestThenReload } from '@common/api';
import '@common/styles.css';
import { ChatMessage, Content, ContextRecord, empty_content } from '@common/types';
import { SingleQueryForm } from '@common/components/SingleQueryForm';
import { ChatForm } from '@common/components/ChatForm';

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
    <><AppNameForm content={content} />
      <div className="content-block">

        <KnowledgeBase content={content} />
        <LLM content={content} />
      </div>
      <TryLLMBlock />
      <div className="content-block">
        <RetrievalEvaluation />
      </div></>
  );
};

const AppNameForm = ({ content }: {
  content: Content
}) => {
  const [appName, setAppName] = useState('');

  const handleSubmit = (event: { preventDefault: () => void; }) => {
    event.preventDefault();
    return jsonRequestThenReload('/api/update-app-name', { app_name: appName });
  };

  return (
    <div className="content-block">
      <div className="content-pane single-pane">
        <h2>RAG Application: {content.app_name}</h2>
        <form id="appNameForm" onSubmit={handleSubmit}>
          <div className="field-group">
            <label>Set a new application name:</label>
            <input type="text" value={appName} onChange={(e) => setAppName(e.target.value)} placeholder={content.app_name} />
            <input type="submit" value="Rename" />
          </div>
        </form>
        <h3>Saved to Repo {content.repo_name}</h3>
      </div>
    </div>
  );
};

const KnowledgeBase = ({ content }: { content: Content }) => {
  const [file, setFile] = useState<File | null>(null);

  const handleFileUpload = (event: { preventDefault: () => void; }) => {
    event.preventDefault();
    const formData = new FormData();
    formData.append('file', file!);
    fetch(buildUrl('/upload'), {
      method: 'POST',
      body: formData,
    }).then(() => {
      window.location.reload();
    });
  };

  return (
    <div className="content-pane">
      <h2>Knowledge-base (for retrieval)</h2>
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
        <div className="field-group">
          <label>Upload file:</label>
          <form id="fileUploadForm" onSubmit={handleFileUpload}>
            <input type="file" onChange={(e) => setFile(e.target.files![0])} />
            <input type="submit" value="Upload" />
          </form>
        </div>
      </div>
    </div>
  );
};

const LLM = ({ content }: { content: Content }) => {
  const [modelName, setModelName] = useState('');

  const handleModelSubmit = (event: React.ChangeEvent<never>) => {
    event.preventDefault();
    return jsonRequestThenReload('/api/update-model', { model_name: modelName });
  };

  return (
    <div className="content-pane">
      <h2>LLM (for generation)</h2>
      <div>
        <div className="field-group">
          <label>Model name:</label>
          <input type="text" value={content.llm_model} disabled />
        </div>
        <form id="llmModelForm" onSubmit={handleModelSubmit}>
          <div className="field-group">
            <label>Change the model:</label>
            <input type="text" value={modelName} onChange={(e) => setModelName(e.target.value)} placeholder={content.llm_model} />
            <input type="submit" value="Change" />
          </div>
        </form>
        <QueryTemplateForm content={content} />
        <ChatTemplateForm content={content} />
      </div>
    </div>
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
    <div className="field-group">
      <label>{label}</label>
      <textarea value={currentVal} onChange={(e) => { onChange(e.target.value) }} />
    </div>
  );
};

const QueryTemplateForm = ({ content }: { content: Content }) => {
  const [newQaTemplate, setQATemplate] = useState(content.query_prompts.text_qa_template);
  const [refineTemplate, setRefineTemplate] = useState(content.query_prompts.refine_template);

  const handleSubmit = (event: React.ChangeEvent<never>) => {
    event.preventDefault();

    return jsonRequestThenReload('/api/update-query-prompts', { text_qa_template: newQaTemplate, refine_template: refineTemplate });
  };

  return (
    <form id="queryTemplateForm" onSubmit={handleSubmit}>
      <h4>Query prompts</h4>
      <div className="field-group">
        <TextAreaFieldGroup label="Question answering:" currentVal={newQaTemplate} onChange={setQATemplate} initialVal={content.query_prompts.text_qa_template} />
      </div>
      <div className="field-group">
        <TextAreaFieldGroup label="Use more context to refine:" currentVal={refineTemplate} onChange={setRefineTemplate} initialVal={content.query_prompts.refine_template} />
      </div>
      <input type="submit" value="Update query prompts" />
    </form>
  );
}

const TryLLMBlock = () => {
  const [completion, setCompletion] = useState('');
  const [queryContexts, setQueryContexts] = useState<ContextRecord[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'system', content: 'You are a helpful assistant.' },
  ]);
  const [chatContexts, setChatContexts] = useState<ContextRecord[]>([]);

  const handleSubmitQuery = async (prompt: string) => {
    const data = await jsonRequest('/api/try-completion', { prompt });
    const typedData = data as { completion: string; contexts: ContextRecord[]; };
    setCompletion(typedData.completion);
    setQueryContexts(typedData.contexts);
  };
  const handleSubmitChat = (messagesToSend: ChatMessage[]) => {
    return jsonRequest('/api/try-chat', { messages: messagesToSend })
      .then((data) => {
        const typedData = data as { completion: string, contexts: ContextRecord[] };
        setMessages([...messagesToSend, { role: 'assistant', content: typedData.completion }]);
        setChatContexts(typedData.contexts);
      });
  };

  return (<div className="content-block">
    <SingleQueryForm completion={completion} contexts={queryContexts} handleSubmit={handleSubmitQuery} />
    <ChatForm prevMessages={messages} contexts={chatContexts} handleSubmitChat={handleSubmitChat} key={messages.length} />
  </div>);
}

const ChatTemplateForm = ({ content }: { content: Content }) => {
  const [contextPrompt, setContextPrompt] = useState(content.chat_prompts.context_prompt);
  const [condensePrompt, setCondensePrompt] = useState(content.chat_prompts.condense_prompt);

  const handleSubmit = (event: { preventDefault: () => void; }) => {
    event.preventDefault();
    return jsonRequestThenReload('/api/update-chat-prompts', { context_prompt: contextPrompt, condense_prompt: condensePrompt });
  };

  return (
    <form id="chatTemplateForm" onSubmit={handleSubmit}>
      <h4>Chat prompts</h4>
      <TextAreaFieldGroup label="Complete next chat:" currentVal={contextPrompt} onChange={setContextPrompt} initialVal={content.chat_prompts.context_prompt} />
      <TextAreaFieldGroup label="Build a question based on history & context" currentVal={condensePrompt} onChange={setCondensePrompt} initialVal={content.chat_prompts.condense_prompt} />
      <input type="submit" value="Update chat prompts" />
    </form>
  );
}

const RetrievalEvaluation = () => {
  return (
    <div className="content-pane single-pane">
      <a href="/evaluation/"><h2>Retrieval evaluation</h2></a>
    </div>
  );
};

export default App;