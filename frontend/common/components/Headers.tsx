
function withCommonClasses(extraClasses: string[] = [], ...classes: string[]) {
    return ["font-bold", ...classes, ...extraClasses].join(' ');
}

export const H1 = ({ text, extraClasses }: { text: string, extraClasses?: string[] }) => {
    return (
        <h1 className={withCommonClasses(extraClasses)}>{text}</h1>
    );
}

export const H2 = ({ text, extraClasses }: { text: string, extraClasses?: string[] }) => {
    return (
        <h2 className={withCommonClasses(extraClasses, "text-2xl underline")}>{text}</h2>
    );
}

export const H3 = ({ text, extraClasses }: { text: string, extraClasses?: string[] }) => {
    return (
        <h3 className={withCommonClasses(extraClasses)}>{text}</h3>
    );
}

export const H4 = ({ text, extraClasses }: { text: string, extraClasses?: string[] }) => {
    return (
        <h4 className={withCommonClasses(extraClasses)}>{text}</h4>
    );
}