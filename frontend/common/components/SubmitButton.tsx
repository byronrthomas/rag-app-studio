
export type SubmitButtonProps = {
    text: string;
    disabled?: boolean;
    extraClasses?: string[];
}

export const SubmitButton = ({ text, disabled, extraClasses }: SubmitButtonProps) => {
    const extraClassesString = extraClasses ? extraClasses.join(' ') : '';
    const disabledChoice = disabled || false;
    return (
        <input className={`px-6 font-semibold border-2 border-black bg-green text-whitesmoke disabled:bg-whitesmoke disabled:text-gray-med disabled:border-0 hover:cursor-pointer ${extraClassesString}`} type="submit" value={text} disabled={disabledChoice} />
    );
}