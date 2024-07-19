import React, { useContext, useState } from 'react';
import '@common/styles.css';
import { jsonRequest } from '@common/api';
import { IsLoadingContext } from '@common/components/IsLoadingContext';
import { LoadingOverlayProvider } from '@common/components/LoadingOverlayProvider';

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

const LaunchAutoRunButton = ({ onResultsReturned }: { onResultsReturned: (d: RetrievalEvalResult[]) => void }) => {
  const setSubmitting = useContext(IsLoadingContext);
  const onError = (_: unknown) => {
    setSubmitting(false);
  }
  const onAutoRunClicked = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    return jsonRequest('/api/evaluation/retrieval/autorun', {}, onError)
      .then((data) => {
        setSubmitting(false);
        onResultsReturned(data as RetrievalEvalResult[]);
      });
  };

  return <button className="px-6 font-semibold border-2 border-black bg-green text-whitesmoke disabled:bg-whitesmoke disabled:text-gray-med disabled:border-0" onClick={onAutoRunClicked}>Run retrieval auto-evaluation</button>;
}

const App = () => {
  const [results, setResults] = useState<RetrievalEvalResult[]>([]);



  return (
    <LoadingOverlayProvider>
      <LaunchAutoRunButton onResultsReturned={setResults} />
      <ResultsTable results={results} />
    </LoadingOverlayProvider>
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