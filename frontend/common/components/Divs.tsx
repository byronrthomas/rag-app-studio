// @ts-expect-error props-can-be-anything
export const LightBorderedDiv = (props) => {
    const extraClassStr = props.extraClasses ? props.extraClasses.join(' ') : '';
    return (
        <div className={`border rounded-sm p-6 shadow-gray-med ${extraClassStr}`}>
            {props.children}
        </div>
    )
}

// @ts-expect-error props-can-be-anything
export const ContentBlockDiv = (props) => {
    const extraClassStr = props.extraClasses ? props.extraClasses.join(' ') : '';
    return (
        <div className={`border-2 p-8 bg-gray-panel-bg ${extraClassStr}`}>
            {props.children}
        </div>
    )
}