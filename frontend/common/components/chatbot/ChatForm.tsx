import { ChatMessage, ContextRecord } from "@common/types";
import { useState } from "react";
import { SubmitButton } from "../SubmitButton";
import { ExistingMsgPanel, YouMsgPanel } from "./MessagePanels";
import { ContextDebugPanel } from "./ContextDebugPanel";
import { LightBorderedDiv } from "../Divs";

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
            <LightBorderedDiv>
                {prevMessages.map((message, index) => (
                    <ExistingMsgPanel key={index} message={message} />))}
                <YouMsgPanel value={nextMessage.content} onChange={(e) => handleMessageChange(e.target.value)} />
                <SubmitButton text="Send" />
            </LightBorderedDiv>
            <ContextDebugPanel contexts={contexts} />
        </form>
    );
};