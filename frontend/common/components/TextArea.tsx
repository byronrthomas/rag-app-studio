import { TextareaAutosize } from "@mui/base";

export type TextAreaProps = {
    value: string;
    disabled?: boolean;
    onChange?: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
    extraClasses?: string[];
}

export const TextArea = ({ value, disabled, onChange, extraClasses }: TextAreaProps) => {
    const classes = ["px-1", "border", "border-gray-med", ...(extraClasses || [])];
    return <TextareaAutosize className={classes.join(' ')} value={value} onChange={onChange} disabled={disabled || false} />
}