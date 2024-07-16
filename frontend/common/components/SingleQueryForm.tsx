import { ContextRecord } from "@common/types";
import { useState } from "react";

export const SingleQueryForm = ({ completion, contexts, handleSubmit: handleSubmitQuery }: { completion: string, contexts: ContextRecord[], handleSubmit: (prompt: string) => void }) => {
    const [prompt, setPrompt] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        handleSubmitQuery(prompt);
    }

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