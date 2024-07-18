import { useState } from "react";
import { H4 } from "../Headers";

const DEFAULT_TEMPERATURE = 0.7;
const DEFAULT_PRESENCE_PENALTY = 0.0;
const DEFAULT_FREQUENCY_PENALTY = 0.0;
const DEFAULT_MAX_TOKENS = -1;
export const DEFAULT_MODEL_PARAMS = {
    temperature: DEFAULT_TEMPERATURE,
    presence_penalty: DEFAULT_PRESENCE_PENALTY,
    frequency_penalty: DEFAULT_FREQUENCY_PENALTY,
    max_tokens: DEFAULT_MAX_TOKENS
};


export const ModelParamsPanel = (props) => {
    const [isDisabled, setIsDisabled] = useState(true);

    const toggleDisabled = () => {
        setIsDisabled(!isDisabled);
    }

    const handleChange = (key: string, event: React.ChangeEvent<HTMLInputElement>) => {
        const newParams = { ...props.modelParams };
        newParams[key] = event.target.value;
        props.onModelParamsChange(newParams);
    }

    return (
        <div className="flex flex-col">
            <div className="flex flex-row my-2">
                <input type="checkbox" id="enableSettings" name="enableSettings" value="0" onChange={toggleDisabled} />
                <H4 text="DANGER: change model settings" extraClasses={["mx-2"]} />
            </div>
            <div className="border rounded-sm p-6 shadow-gray-med my-0">
                <div className="flex flex-row justify-between">
                    <label>Temperature:</label>
                    <input className="w-64" type="number" value={props.modelParams.temperature} disabled={isDisabled} onChange={(e) => handleChange("temperature", e)} />
                </div>
                <div className="flex flex-row justify-between my-2">
                    <label>Presence penalty:</label>
                    <input className="w-64" type="number" value={props.modelParams.presence_penalty} disabled={isDisabled} onChange={(e) => handleChange("presence_penalty", e)} />
                </div>
                <div className="flex flex-row justify-between">
                    <label>Frequency penalty:</label>
                    <input className="w-64" type="number" value={props.modelParams.frequency_penalty} disabled={isDisabled} onChange={(e) => handleChange("frequency_penalty", e)} />
                </div>
                <div className="flex flex-row justify-between my-2">
                    <label>Max tokens:</label>
                    <input className="w-64" type="number" value={props.modelParams.max_tokens} disabled={isDisabled} onChange={(e) => handleChange("max_tokens", e)} />
                </div>

                <div>
                    Refer to <a href="https://platform.openai.com/docs/api-reference/chat/create">Open AI API documentation for more information</a>
                </div>
            </div>
        </div>

    )
}