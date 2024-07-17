import { ContextRecord } from "@common/types";
import { useState } from "react";
import { H4 } from "../Headers";

export const ContextDebugPanel = ({ contexts }: { contexts: ContextRecord[]; }) => {
    const [includeContexts, setIncludeContexts] = useState(false);

    const toggleContexts = (_e: React.ChangeEvent) => {
        setIncludeContexts(!includeContexts);
    };

    return (
        <>
            <div className="flex flex-row my-4">
                <input type="checkbox" id="includeContexts" name="includeContexts" value="0" onChange={toggleContexts} />
                <H4 text="[Debug] Context used to answer" extraClasses={["mx-2"]} />
            </div>
            <div id="chatContexts">
                {includeContexts &&
                    (contexts.length > 0 ?

                        contexts.map((context, index) => (
                            <div className="my-4" key={index}>
                                <p className="font-semibold">Score: {context.score} -- File: {context.filename}</p>
                                <hr />
                                {context.context.split('\n').map((line, idx) => (
                                    <p key={idx}>{line}</p>
                                ))}
                            </div>
                        )) :
                        <div>Run a query to see the contexts used</div>)}
            </div>
        </>
    );
};
