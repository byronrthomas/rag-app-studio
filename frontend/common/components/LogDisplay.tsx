import { buildUrl } from "@common/api";
import { useCallback, useState } from "react";
import { H4 } from "./Headers";
import { TextArea } from "./TextArea";

export const LogFooter = ({ logUrl }: { logUrl: string }) => {
    const [displayEnabled, setDisplayEnabled] = useState(false);
    return (
        <div className="flex flex-col gap-4 items-start m-4">
            {displayEnabled ? <button onClick={() => setDisplayEnabled(false)}>Hide logs</button> : <button onClick={() => setDisplayEnabled(true)}>Show logs</button>}
            {displayEnabled && <LogDisplayPane url={logUrl} />}
        </div>
    );
}

const LogDisplayPane = ({ url }: { url: string }) => {
    const [logs, setLogs] = useState([]);
    const [linesToFetch, setLinesToFetch] = useState(100);
    const fetchLogs = useCallback(() => {
        fetch(buildUrl(`${url}?num_lines=${linesToFetch}`))
            .then(response => response.json())
            .then(data => setLogs(data.logs))
            .catch(error => { console.error('Error fetching logs:', error); alert("Something wrong - is server working correctly, failed to fetch logs"); });
    }, [url, linesToFetch]);

    const formatForDisplay = (logs: string[]) => {
        // log lines terminate with newline
        return logs.join('');
    }

    return (
        <>
            <div className="flex flex-row gap-4">
                <H4 text="Server logs" />

                <input className="w-16" type="number" value={linesToFetch} onChange={(e) => setLinesToFetch(parseInt(e.target.value))} min={10} max={10000} step={10} />
                <label>Lines</label>
                <button className="px-6 font-semibold border-2 border-black bg-green text-whitesmoke hover:cursor-pointer" onClick={fetchLogs}>Fetch</button>
            </div >
            <TextArea extraClasses={["w-full"]} value={formatForDisplay(logs)} />
            <div>


            </div>

        </>
    );
}