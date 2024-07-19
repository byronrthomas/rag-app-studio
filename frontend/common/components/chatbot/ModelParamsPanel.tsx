import { useState } from "react";
import { DEFAULT_MODEL_PARAMS, ModelParams } from "./ModelParams";


export const ModelParamsPanel = (props: { onModelParamsChange: (arg0: ModelParams) => void; modelParams: ModelParams; }) => {
    const [isDisabled, setIsDisabled] = useState(true);

    const handleSettingsEnable = () => {
        setIsDisabled(false);
    }

    const handleSettingsReset = () => {
        setIsDisabled(true);
        props.onModelParamsChange(DEFAULT_MODEL_PARAMS);
    }

    const handleChange = (key: string, event: React.ChangeEvent<HTMLInputElement>) => {
        const newParams = { ...props.modelParams };
        // @ts-expect-error key-is-string
        newParams[key] = event.target.value;
        // console.log("newParams", newParams);
        props.onModelParamsChange(newParams);
    }

    return (
        <div className="flex flex-col">

            <div className="border rounded-sm p-8 shadow-gray-med space-y-2">
                <div className="flex flex-row">
                    {isDisabled ?
                        <button className="w-full bg-gold border-2 text-green px-6 font-semibold hover:cursor-pointer" onClick={handleSettingsEnable}>DANGER: change inference settings</button>
                        : <button className="w-full px-6 font-semibold border-2 border-black bg-green text-whitesmoke hover:cursor-pointer" onClick={handleSettingsReset}>Return to default settings</button>
                    }

                </div>
                <div className="flex flex-row justify-between">
                    <label>Temperature:</label>
                    <input className="w-64" type="number" value={props.modelParams.temperature} disabled={isDisabled} onChange={(e) => handleChange("temperature", e)} min={0.0} max={2.0} step={0.1} />
                </div>
                <div className="flex flex-row justify-between my-2">
                    <label>Presence penalty:</label>
                    <input className="w-64" type="number" value={props.modelParams.presence_penalty} disabled={isDisabled} onChange={(e) => handleChange("presence_penalty", e)} min={-2.0} max={2.0} step={0.1} />
                </div>
                <div className="flex flex-row justify-between">
                    <label>Frequency penalty:</label>
                    <input className="w-64" type="number" value={props.modelParams.frequency_penalty} disabled={isDisabled} onChange={(e) => handleChange("frequency_penalty", e)} min={-2.0} max={2.0} step={0.1} />
                </div>
                <div className="flex flex-row justify-between my-2">
                    <label>Max tokens:</label>
                    <input className="w-64" type="number" value={props.modelParams.max_tokens} disabled={isDisabled} onChange={(e) => handleChange("max_tokens", e)} min={10} max={1024} step={1} />
                </div>

                <div>
                    Refer to <a className="text-blue" href="https://platform.openai.com/docs/api-reference/chat/create">Open AI API documentation for more information</a>
                </div>
            </div>
        </div >

    )
}