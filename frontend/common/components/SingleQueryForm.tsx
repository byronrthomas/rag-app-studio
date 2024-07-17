import { ContextRecord } from "@common/types";
import { useState } from "react";
import { SubmitButton } from "./SubmitButton";
import { H4 } from "./Headers";
import { ExistingMsgPanel, YouMsgPanel } from "./chatbot/MessagePanels";

export const SingleQueryForm = ({ completion, contexts, handleSubmit: handleSubmitQuery }: { completion: string, contexts: ContextRecord[], handleSubmit: (prompt: string) => void }) => {
    const [prompt, setPrompt] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        handleSubmitQuery(prompt);
    }

    return (
        <form id="completionForm" onSubmit={handleSubmit}>
            <div className="border rounded p-6">
                <YouMsgPanel value={prompt} onChange={(e) => setPrompt(e.target.value)} />
                <ExistingMsgPanel message={{ role: 'assistant', content: completion }} />
                <SubmitButton text="Answer query" />
            </div>


            <H4 text="Retrieved texts for last query:" />
            <div id="queryContexts">
                {contexts.map((context, index) => (
                    <div key={index}>
                        <p>Score: {context.score} -- File: {context.filename}</p>
                        <p>{context.context}</p>
                    </div>
                ))}
            </div>
        </form>
    );
};