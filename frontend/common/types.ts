export type ContextRecord = {
    score: number;
    filename: string;
    context: string;
};
export type Content = {
    app_name: string;
    repo_name: string;
    embed_model: string;
    files: string[];
    last_checkpoint: string;
    query_prompts: {
        text_qa_template: string;
        refine_template: string;
    };
    chat_prompts: {
        context_prompt: string;
        condense_prompt: string;
    };
    llm_model: string;
    completion: string;
};
export const empty_content: Content = {
    app_name: '',
    repo_name: '',
    embed_model: '',
    files: [],
    last_checkpoint: '',
    query_prompts: {
        text_qa_template: '',
        refine_template: '',
    },
    chat_prompts: {
        context_prompt: '',
        condense_prompt: '',
    },
    llm_model: '',
    completion: ''
};

export type ChatMessage = {
    role: 'user' | 'assistant' | 'system';
    content: string;
};
