
function withCommonClasses(...classes: string[]) {
    return ["font-bold", ...classes].join(' ');
}

export const H1 = ({ text }: { text: string }) => {
    return (
        <h1 className={withCommonClasses()}>{text}</h1>
    );
}

export const H2 = ({ text }: { text: string }) => {
    return (
        <h2 className={withCommonClasses("text-2xl underline")}>{text}</h2>
    );
}

export const H3 = ({ text }: { text: string }) => {
    return (
        <h3 className={withCommonClasses()}>{text}</h3>
    );
}

export const H4 = ({ text }: { text: string }) => {
    return (
        <h4 className={withCommonClasses()}>{text}</h4>
    );
}