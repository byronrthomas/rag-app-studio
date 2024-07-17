import { ChatMessage, ContextRecord } from "@common/types";
import { useState } from "react";
import { H4 } from "./Headers";
import { SubmitButton } from "./SubmitButton";
import { ExistingMsgPanel, YouMsgPanel } from "./chatbot/MessagePanels";


export const ChatForm = ({ prevMessages, contexts, handleSubmitChat }: { prevMessages: ChatMessage[], contexts: ContextRecord[], handleSubmitChat: (messagesToSend: ChatMessage[]) => void }) => {
    const [nextMessage, setNextMessage] = useState<ChatMessage>({ role: 'user', content: '....' });

    const handleMessageChange = (content: string) => {
        setNextMessage({ ...nextMessage, content });
    };

    const handleSubmit = (event: { preventDefault: () => void; }) => {
        event.preventDefault();
        handleSubmitChat([...prevMessages, nextMessage]);
    };


    return (
        <form id="chatForm" onSubmit={handleSubmit}>
            <div className="border rounded p-6">
                {prevMessages.map((message, index) => (
                    <ExistingMsgPanel key={index} message={message} />))}
                <YouMsgPanel value={nextMessage.content} onChange={(e) => handleMessageChange(e.target.value)} />
                <SubmitButton text="Send" />
            </div>
            <SubmitButton text="Respond to chat" />
            <H4 text="Retrieved texts for last query:" />
            <div id="chatContexts">
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