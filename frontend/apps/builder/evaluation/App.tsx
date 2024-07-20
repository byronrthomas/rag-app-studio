import React, { useContext, useState } from 'react';
import '@common/styles.css';
import { jsonRequest } from '@common/api';
import { IsLoadingContext } from '@common/components/IsLoadingContext';
import { LoadingOverlayProvider } from '@common/components/LoadingOverlayProvider';
import { Popper } from '@mui/base/Popper';

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
      <div className='my-4'>
        <ResultsTable results={results} />
      </div>
    </LoadingOverlayProvider>
  );
};

const HeaderCell = ({ text }: { text: string }) => {
  return <th className="border border-gray-dark bg-gray-med">{text}</th>;
}

const DataCell = ({ text }: { text: string }) => {
  return <td className="border border-gray-med">{text}</td>;
}

const shortenText = (text: string) => {
  return text.length > 50 ? text.substring(0, 50) + "..." : text;
}
const LongTextDataCell = ({ fullText, onClick }: { fullText: string, onClick: (e: React.MouseEvent<HTMLElement>, text: string) => void }) => {
  const text = shortenText(fullText);
  const clickable = (text != fullText) || text.indexOf("\n") > -1;
  const classes = clickable ? "border border-gray-med hover:cursor-pointer" : "border border-gray-med";
  return <td className={classes} onClick={(e) => onClick(e, fullText)}>{text}</td>;
}

const ResultsTable = ({ results }: { results: RetrievalEvalResult[] }) => {
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const [fullText, setFullText] = React.useState("");
  const formatNumber = (num: number) => {
    return num.toFixed(3);
  }


  const handleClick = (event: React.MouseEvent<HTMLElement>, fullText: string) => {
    setAnchorEl(anchorEl ? null : event.currentTarget);
    setFullText(fullText);
  };

  const popperOpen = Boolean(anchorEl);
  const id = popperOpen ? 'simple-popper' : undefined;
  return (
    <><table className="w-full table-auto border-collapse border border-gray-med bg-whitesmoke">
      <thead>
        <tr>
          <HeaderCell text="Query" />
          <HeaderCell text="Expected" />
          <HeaderCell text="Retrieved 0" />
          <HeaderCell text="Retrieved 1" />
          <HeaderCell text="Precision" />
          <HeaderCell text="Recall" />
          <HeaderCell text="Hit rate" />
        </tr>
      </thead>
      <tbody>
        {results.map((result, i) => {
          return (
            <tr key={i}>
              <LongTextDataCell fullText={result.query} onClick={handleClick} />
              <LongTextDataCell fullText={result.expected_texts[0]} onClick={handleClick} />
              <LongTextDataCell fullText={result.retrieved_texts[0]} onClick={handleClick} />
              <LongTextDataCell fullText={result.retrieved_texts[1]} onClick={handleClick} />
              <DataCell text={formatNumber(result.metrics.precision)} />
              <DataCell text={formatNumber(result.metrics.recall)} />
              <DataCell text={formatNumber(result.metrics.hit_rate)} />
            </tr>
          );
        })}
      </tbody>
    </table><Popper id={id} open={popperOpen} anchorEl={anchorEl}>
        <div className="p-2 bg-gray-med text-whitesmoke">{fullText}</div>
      </Popper></>
  );
}

export default App;