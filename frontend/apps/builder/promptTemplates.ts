export const CHAT_QUESTION_TEMPLATE = `
  The following is a friendly conversation between a user and an AI assistant.
  The assistant is talkative and provides lots of specific details from its context.
  If the assistant does not know the answer to a question, it truthfully says it
  does not know.

  Here are the relevant documents for the context:

  {context_str}

  Instruction: Based on the above documents, provide a detailed answer for the user question below.
  Answer "don't know" if not present in the document.
  `

export const CHAT_CONDENSE_TEMPLATE = `
  Given the following conversation between a user and an AI assistant and a follow up question from user,
  rephrase the follow up question to be a standalone question.

  Chat History:
  {chat_history}
  Follow Up Input: {question}
  Standalone question:`

export const QUERY_QA_TEMPLATE = `Context information is below.
---------------------
{context_str}
---------------------
Given the context information and not prior knowledge, answer the query.
Query: {query_str}
Answer: `

export const QUERY_REFINE_TEMPLATE = `The original query is as follows: {query_str}
We have provided an existing answer: {existing_answer}
We have the opportunity to refine the existing answer (only if needed) with some more context below.
------------
{context_msg}
------------
Given the new context, refine the original answer to better answer the query. If the context isn't useful, return the original answer.
Refined Answer: `