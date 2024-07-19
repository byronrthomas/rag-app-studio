import { buildUrl } from "@common/api";
import { Content } from "@common/types";
import { useMemo, useState } from "react";
import { LightBorderedDiv } from "./Divs";
import { H2 } from "./Headers";
import { FileTable } from "./FileTable";
import { SpinnerOverlay } from "./SpinnerOverlay";
import Uploady, { Batch, UPLOADER_EVENTS } from "@rpldy/uploady";
import UploadButton from "@rpldy/upload-button";
import { primaryButtonClasses } from "./PrimaryButton";

export const KnowledgeBasePanel = ({ content, allowUpload }: { content: Content, allowUpload?: boolean }) => {
    const [isSubmitting, setIsSubmitting] = useState(false);

    const uploadShown = allowUpload ?? false;

    const listeners = useMemo(() => ({
        [UPLOADER_EVENTS.BATCH_START]: (batch: Batch) => {
            setIsSubmitting(true);
            console.log(`Uploading - Batch Start - ${batch.id} - item count = ${batch.items.length}`);
        },
        [UPLOADER_EVENTS.BATCH_FINALIZE]: (batch: Batch) => {
            setIsSubmitting(false);
            console.log(`Uploading - Batch Finish - ${batch.id} - item count = ${batch.items.length}`);
        },
        [UPLOADER_EVENTS.BATCH_ERROR]: (batch: Batch) => {
            alert(`Error: only uploaded ${batch.completed} items. Please adjust your request and try again.`);
        },

        [UPLOADER_EVENTS.BATCH_FINISH]: (batch: Batch) => {
            setIsSubmitting(false);
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

    return (
        <>
            <SpinnerOverlay isVisible={isSubmitting} />
            <LightBorderedDiv extraClasses={["w-1/2"]}>
                <H2 text="Knowledge-base (for retrieval)" />
                <div className="my-4">
                    <div className="flex flex-row justify-between my-2">
                        <label>Current embedding model:</label>
                        <input className="w-80" type="text" value={content.embed_model} disabled />
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
