import React, { useState, useEffect } from 'react';
import { buildUrl, jsonRequest, jsonRequestThenReload } from '@common/api';
import '@common/styles.css';

type Content = {
  app_name: string;
  repo_name: string;
  embed_model: string;
  files: string[];
  last_checkpoint: string;
  query_prompts: {
    text_qa_template: string;
    refine_template: string;
  };
  chat_prompts: {
    context_prompt: string;
    condense_prompt: string;
  };
  llm_model: string;
  completion: string;
};

const empty_content: Content = {
  app_name: '',
  repo_name: '',
  embed_model: '',
  files: [],
  last_checkpoint: '',
  query_prompts: {
    text_qa_template: '',
    refine_template: '',
  },
  chat_prompts: {
    context_prompt: '',
    condense_prompt: '',
  },
  llm_model: '',
  completion: ''
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
    <><AppNameForm content={content} />
      <div className="content-block">

        <KnowledgeBase content={content} />
        <LLM content={content} />
      </div>
      <div className="content-block">
        <SingleQueryForm content={content} />
        <ChatForm />
      </div>
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
    return jsonRequestThenReload('/update-app-name', { app_name: appName });
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
    return jsonRequestThenReload('/update-model', { model_name: modelName });
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
      console.log('initialVal has changed - ', initialVal, lastInitialVal);

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

    return jsonRequestThenReload('/update-query-prompts', { text_qa_template: newQaTemplate, refine_template: refineTemplate });
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

const ChatTemplateForm = ({ content }: { content: Content }) => {
  const [contextPrompt, setContextPrompt] = useState(content.chat_prompts.context_prompt);
  const [condensePrompt, setCondensePrompt] = useState(content.chat_prompts.condense_prompt);

  const handleSubmit = (event: { preventDefault: () => void; }) => {
    event.preventDefault();
    return jsonRequestThenReload('/update-chat-prompts', { context_prompt: contextPrompt, condense_prompt: condensePrompt });
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

type ContextRecord = {
  score: number;
  filename: string;
  context: string;
};

const SingleQueryForm = ({ content }: { content: Content }) => {
  const [prompt, setPrompt] = useState('');
  const [completion, setCompletion] = useState(content.completion);
  const [contexts, setContexts] = useState<ContextRecord[]>([]);

  const handleSubmit = (event: { preventDefault: () => void; }) => {
    event.preventDefault();
    return jsonRequest('/try-completion', { prompt })
      .then((data: unknown) => {
        const typedData = data as { completion: string, contexts: ContextRecord[] };
        setCompletion(typedData.completion);
        setContexts(typedData.contexts);
      });
  };

  return (
    <div className="content-pane">
      <h2>Try a single query:</h2>
      <form id="completionForm" onSubmit={handleSubmit}>
        <div className="field-group">
          <label>Prompt (no history):</label>
          <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} />
        </div>
        <div className="field-group">
          <label>Last response:</label>
          <textarea value={completion} disabled />
        </div>
        <input type="submit" value="Answer query" />
        <h4>Retrieved texts for last query:</h4>
        <div id="queryContexts">
          {contexts.map((context, index) => (
            <div key={index}>
              <p>Score: {context.score} -- File: {context.filename}</p>
              <p>{context.context}</p>
            </div>
          ))}
        </div>
      </form>
    </div>
  );
};

const ChatForm = () => {
  const [messages, setMessages] = useState([
    { role: 'system', content: 'You are a helpful assistant.' },
    { role: 'user', content: '....' }
  ]);
  const [contexts, setContexts] = useState<ContextRecord[]>([]);

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    return jsonRequest('/try-chat', { messages })
      .then((data) => {
        const typedData = data as { completion: string, contexts: ContextRecord[] };
        setMessages([...messages, { role: 'assistant', content: typedData.completion }, { role: 'user', content: '' }]);
        setContexts(typedData.contexts);
      });
  };

  const handleMessageChange = (index: number, content: string) => {
    const newMessages = [...messages];
    newMessages[index].content = content;
    setMessages(newMessages);
  };

  return (
    <div className="content-pane">
      <h2>Try a chat</h2>
      <form id="chatForm" onSubmit={handleSubmit}>
        <div id="chatMessages">
          {messages.map((message, index) => (
            <div className="field-group" key={index}>
              <label>{message.role}</label>
              <textarea value={message.content} onChange={(e) => handleMessageChange(index, e.target.value)} />
            </div>
          ))}
        </div>
        <input type="submit" value="Respond to chat" />
        <h4>Retrieved texts for last query:</h4>
        <div id="chatContexts">
          {contexts.map((context, index) => (
            <div key={index}>
              <p>Score: {context.score} -- File: {context.filename}</p>
              <p>{context.context}</p>
            </div>
          ))}
        </div>
      </form>
    </div>
  );
};

const RetrievalEvaluation = () => {
  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    fetch('/retrieval_eval_autorun_view', {
      method: 'POST',
    }).then(() => {
      window.location.reload();
    });
  };

  return (
    <div className="content-pane single-pane">
      <h2>Retrieval evaluation</h2>
      <div className="field-group">
        <label>Run retrieval auto-evaluation:</label>
        <form id="evalRunForm" onSubmit={handleSubmit} target="_blank">
          <input type="submit" value="Run" />
        </form>
      </div>
    </div>
  );
};

export default App;