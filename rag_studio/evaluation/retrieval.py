from llama_index.core.evaluation import (
    generate_question_context_pairs,
    RetrieverEvaluator,
)
from llama_index.core.evaluation.retrieval.metrics import METRIC_REGISTRY

ALL_METRICS = [k for k in METRIC_REGISTRY.keys() if k != "cohere_rerank_relevancy"]


def build_evaluator(query_engine):
    return RetrieverEvaluator.from_metric_names(
        ALL_METRICS, retriever=query_engine.retriever
    )


def auto_generate_dataset(llm, nodes):
    return generate_question_context_pairs(nodes, llm=llm, num_questions_per_chunk=2)


async def evaluate_on_auto_dataset(query_engine, llm, nodes):
    evaluator = build_evaluator(query_engine)
    dataset = auto_generate_dataset(llm, nodes)
    return await evaluator.aevaluate_dataset(dataset)
