import { ChatMessage } from "@common/types";
import { TextArea, TextAreaProps } from "../TextArea";

export const YouMsgPanel = (props: TextAreaProps) => (
    <div className="flex flex-col my-2">
        <div className="flex flex-row-reverse px-2">
            <label className="font-semibold text-green">You</label>
        </div>
        <TextArea {...props} />
    </div>
);

export const ExistingMsgPanel = ({ message }: { message: ChatMessage }) => {
    if (message.role === 'user') {
        return <YouMsgPanel value={message.content} disabled />;
    }
    const lblTextForRole = message.role === 'assistant' ? 'BOT' : 'SYS';
    return (
        <div className="flex flex-col my-2">
            <div className="flex flex-row px-2">
                <label className="font-semibold text-red">{lblTextForRole}</label>
            </div>
            <TextArea value={message.content} disabled />
        </div>
    );
}