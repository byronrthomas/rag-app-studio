import { ChatMessage, ContextRecord } from "@common/types";
import { useState } from "react";

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
        <div className="content-pane">
            <h2>Try a chat</h2>
            <form id="chatForm" onSubmit={handleSubmit}>
                <div id="chatMessages">
                    {prevMessages.map((message, index) => (
                        <div className="field-group" key={index}>
                            <label>{message.role}</label>
                            <textarea value={message.content} disabled={true} />
                        </div>
                    ))}
                    <div className='field-group'>
                        <label>{nextMessage.role}</label>
                        <textarea value={nextMessage.content} onChange={(e) => handleMessageChange(e.target.value)} />

                    </div>
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