export type ModelParams = {
    temperature: number;
    presence_penalty: number;
    frequency_penalty: number;
    max_tokens: number;
};

const DEFAULT_TEMPERATURE = 0.7;
const DEFAULT_PRESENCE_PENALTY = 0.0;
const DEFAULT_FREQUENCY_PENALTY = 0.0;
const DEFAULT_MAX_TOKENS = 512;

export const DEFAULT_MODEL_PARAMS = {
    temperature: DEFAULT_TEMPERATURE,
    presence_penalty: DEFAULT_PRESENCE_PENALTY,
    frequency_penalty: DEFAULT_FREQUENCY_PENALTY,
    max_tokens: DEFAULT_MAX_TOKENS
};

export const validateParams = (params: ModelParams) => {
    return params.temperature >= 0.0 && params.temperature <= 2.0 &&
        params.presence_penalty >= -2.0 && params.presence_penalty <= 2.0 &&
        params.frequency_penalty >= -2.0 && params.frequency_penalty <= 2.0 &&
        params.max_tokens > 0;
};

export const findParamIssues = (params: ModelParams) => {
    const issues = [];
    if (params.temperature < 0.0 || params.temperature > 2.0) {
        issues.push("Temperature must be between 0.0 and 2.0");
    }
    if (params.presence_penalty < -2.0 || params.presence_penalty > 2.0) {
        issues.push("Presence penalty must be between -2.0 and 2.0");
    }
    if (params.frequency_penalty < -2.0 || params.frequency_penalty > 2.0) {
        issues.push("Frequency penalty must be between -2.0 and 2.0");
    }
    if (params.max_tokens <= 0) {
        issues.push("Max tokens must be greater than 0");
    }
    return issues;
};

export const encodeForTransports = (params: ModelParams) => {
    if (!validateParams(params)) {
        throw new Error("Invalid parameters");
    }
    console.log("params", params);
    const toReturn = new Map<string, number>();
    if (params.temperature != DEFAULT_TEMPERATURE) {
        toReturn.set('temperature', params.temperature);
    }
    if (params.presence_penalty != DEFAULT_PRESENCE_PENALTY) {
        toReturn.set('presence_penalty', params.presence_penalty);
    }
    if (params.frequency_penalty != DEFAULT_FREQUENCY_PENALTY) {
        toReturn.set('frequency_penalty', params.frequency_penalty);
    }
    if (params.max_tokens != DEFAULT_MAX_TOKENS) {
        toReturn.set('max_tokens', params.max_tokens);
    }
    console.log("toReturn", toReturn);
    return toReturn;
};

