
export type SubmitButtonProps = {
    text: string;
    disabled?: boolean;
}

export const SubmitButton = ({ text, disabled }: SubmitButtonProps) => {
    const disabledChoice = disabled || false;
    return (
        <input className="px-6 font-semibold border-2 border-black bg-green text-whitesmoke my-4" type="submit" value={text} disabled={disabledChoice} />
    );
}