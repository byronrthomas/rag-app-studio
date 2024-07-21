import { buildUrl, jsonRequestThenReload } from "@common/api";
import { Content } from "@common/types";
import { useContext, useMemo, useState } from "react";
import { LightBorderedDiv } from "./Divs";
import { H2 } from "./Headers";
import { FileTable } from "./FileTable";
import Uploady, { Batch, UPLOADER_EVENTS } from "@rpldy/uploady";
import UploadButton from "@rpldy/upload-button";
import { primaryButtonClasses } from "./PrimaryButton";
import { SubmitButton } from "./SubmitButton";
import { IsLoadingContext } from "./IsLoadingContext";
import { Select, Option } from "@mui/base";

export const KnowledgeBasePanel = ({ content, allowEdits }: { content: Content, allowEdits?: boolean }) => {
    const [embeddingName, setEmbeddingName] = useState('');
    const setSubmitting = useContext(IsLoadingContext);
    const onError = (_: unknown) => {
        setSubmitting(false);
    }

    const uploadShown = allowEdits ?? false;

    const listeners = useMemo(() => ({
        [UPLOADER_EVENTS.BATCH_START]: (batch: Batch) => {
            setSubmitting(true);
            console.log(`Uploading - Batch Start - ${batch.id} - item count = ${batch.items.length}`);
        },
        [UPLOADER_EVENTS.BATCH_FINALIZE]: (batch: Batch) => {
            setSubmitting(false);
            console.log(`Uploading - Batch Finish - ${batch.id} - item count = ${batch.items.length}`);
        },
        [UPLOADER_EVENTS.BATCH_ERROR]: (batch: Batch) => {
            alert(`Error: only uploaded ${batch.completed} items. Please adjust your request and try again.`);
        },

        [UPLOADER_EVENTS.BATCH_FINISH]: (batch: Batch) => {
            setSubmitting(false);
            console.log(`Uploading - Batch Finish - ${batch.id} - item count = ${batch.items.length}`);
            window.location.reload();
        }
    }), []);

    // const dummyFiles = [];
    // for (let i = 0; i < 60; i++) {
    //   const array = new Uint8Array(4);
    //   window.crypto.getRandomValues(array);
    //   const hexToken = Array.from(array).map(b => b.toString(16).padStart(2, '0')).join('');
    //   dummyFiles.push(`file_${hexToken}.txt`);
    // }


    const supportedEmbeddings = [
        "BAAI/bge-small-en-v1.5", "BAAI/bge-base-en-v1.5",
        "BAAI/bge-large-en-v1.5",
    /* multilingual */ "BAAI/bge-m3",
        "sentence-transformers/all-MiniLM-L6-v2",
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"];

    const handleEmbeddingSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        if (embeddingName === content.embed_model) {
            alert("No change detected.");
            return;
        }
        setSubmitting(true);
        await jsonRequestThenReload('/api/update-embedding-model', { embedding_model: embeddingName }, onError);
    }

    const shouldBlockEmbeddingChanges = content.files.length > 0;
    // const shouldBlockEmbeddingChanges = false;

    const enabledOptionClasses = "bg-whitesmoke hover:bg-blue hover:text-whitesmoke";
    return (
        <>
            <LightBorderedDiv extraClasses={["w-1/2"]}>
                <H2 text="Knowledge-base (for retrieval)" />
                <div className="my-4">
                    <div className="space-y-2">
                        <div className="flex flex-row justify-between">
                            <label>Current embedding model:</label>
                            <input className="w-80" type="text" value={content.embed_model} disabled />
                        </div>
                        {allowEdits &&
                            <form id="embedModelForm" onSubmit={handleEmbeddingSubmit}>
                                <div className="flex flex-row justify-between content-center items-center">
                                    <SubmitButton disabled={shouldBlockEmbeddingChanges || !embeddingName || embeddingName === content.embed_model} text="Change" />
                                    <Select className="bg-whitesmoke w-3/4 border border-blue border-2" value={shouldBlockEmbeddingChanges ? "default" : embeddingName} onChange={(_, newValue) => setEmbeddingName(newValue!)} slotProps={{ popup: { className: 'bg-whitesmoke border border-blue border-2 w-auto hover:cursor-pointer' } }} disabled={shouldBlockEmbeddingChanges}>
                                        {shouldBlockEmbeddingChanges ? <Option value="default" disabled>Cannot change embedding model once files uploaded</Option> :
                                            supportedEmbeddings.map((embedding) => (
                                                <Option className={enabledOptionClasses} key={embedding} value={embedding}>{embedding}</Option>
                                            ))}
                                    </Select>


                                </div>
                            </form>
                        }
                    </div>
                    <div className="my-2">
                        <FileTable files={content.files} />
                        {uploadShown &&
                            (<div className="flex flex-row justify-between my-2">
                                <Uploady listeners={listeners} destination={{ url: buildUrl("/api/upload") }} >
                                    <UploadButton className={primaryButtonClasses} text="Upload file(s)" />
                                </Uploady>
                                <Uploady listeners={listeners} destination={{ url: buildUrl("/api/upload") }} webkitdirectory>
                                    <UploadButton className={primaryButtonClasses} text="Upload folder" />
                                </Uploady>

                            </div>
                            )}
                    </div>
                </div>
            </LightBorderedDiv>
        </>
    );
};
