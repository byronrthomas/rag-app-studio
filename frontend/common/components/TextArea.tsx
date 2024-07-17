import { TextareaAutosize } from "@mui/base";

export type TextAreaProps = {
    value: string;
    disabled?: boolean;
    onChange?: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
}

export const TextArea = ({ value, disabled, onChange }: TextAreaProps) => {
    return <TextareaAutosize className="px-1 border border-gray-med" value={value} onChange={onChange} disabled={disabled || false} />
}