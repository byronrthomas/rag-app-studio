
export type PrimaryButtonProps = {
    text: string;
    disabled?: boolean;
    extraClasses?: string[];
    onClick?: () => void;
}

export const primaryButtonClasses = "px-6 font-semibold border-2 border-black bg-green text-whitesmoke disabled:bg-whitesmoke disabled:text-gray-med disabled:border-0 hover:cursor-pointer";

export const PrimaryButton = ({ text, disabled, extraClasses, onClick }: PrimaryButtonProps) => {
    const extraClassesString = extraClasses ? extraClasses.join(' ') : '';
    const disabledChoice = disabled || false;
    return (
        <button className={`${primaryButtonClasses} ${extraClassesString}`} value={text} disabled={disabledChoice} onClick={onClick}>{text}</button>
    );
}