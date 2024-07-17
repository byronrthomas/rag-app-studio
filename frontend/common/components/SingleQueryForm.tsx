import { ContextRecord } from "@common/types";
import { useState } from "react";
import { SubmitButton } from "./SubmitButton";
import { ExistingMsgPanel, YouMsgPanel } from "./chatbot/MessagePanels";
import { ContextDebugPanel } from "./chatbot/ContextDebugPanel";

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
            <ContextDebugPanel contexts={contexts} />
        </form>
    );
};