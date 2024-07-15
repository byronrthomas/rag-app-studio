import React, { useState } from 'react';
import '@common/styles.css';
import { jsonRequest } from '@common/api';

// Response type looks like:
// {
//   "query": eval_result["query"],
//   "expected_text": eval_result["expected_texts"][0],
//   "retrieved_text_0": eval_result["retrieved_texts"][0],
//   "retrieved_text_1": eval_result["retrieved_texts"][1],
//   "precision": eval_result["metrics"]["precision"],
//   "recall": eval_result["metrics"]["recall"],
//   "hit_rate": eval_result["metrics"]["hit_rate"],
// }
type RetrievalEvalResult = {
  query: string;
  expected_texts: string[];
  retrieved_texts: string[];
  metrics: {
    precision: number;
    recall: number;
    hit_rate: number;
  };
};

const App = () => {
  const [results, setResults] = useState<RetrievalEvalResult[]>([]);

  const onAutoRunClicked = (e: React.FormEvent) => {
    e.preventDefault();
    return jsonRequest('/api/evaluation/retrieval/autorun', {})
      .then((data) => {
        setResults(data as RetrievalEvalResult[]);
      });
  };

  return (
    <>
      <button onClick={onAutoRunClicked}>Run retrieval auto-evaluation</button>
      <ResultsTable results={results} />
    </>
  );
};

const ResultsTable = ({ results }: { results: RetrievalEvalResult[] }) => {
  return (
    <table>
      <thead>
        <tr>
          <th>Query</th>
          <th>Expected</th>
          <th>Retrieved 0</th>
          <th>Retrieved 1</th>
          <th>Precision</th>
          <th>Recall</th>
          <th>Hit rate</th>
        </tr>
      </thead>
      <tbody>
        {results.map((result, i) => (
          <tr key={i}>
            <td>{result.query}</td>
            <td>{result.expected_texts[0]}</td>
            <td>{result.retrieved_texts[0]}</td>
            <td>{result.retrieved_texts[1]}</td>
            <td>{result.metrics.precision}</td>
            <td>{result.metrics.recall}</td>
            <td>{result.metrics.hit_rate}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default App;