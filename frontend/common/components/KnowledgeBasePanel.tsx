import { buildUrl } from "@common/api";
import { Content } from "@common/types";
import { useState } from "react";
import { LightBorderedDiv } from "./Divs";
import { H2 } from "./Headers";
import { FileTable } from "./FileTable";
import { SubmitButton } from "./SubmitButton";
import { SpinnerOverlay } from "./SpinnerOverlay";

export const KnowledgeBasePanel = ({ content, allowUpload }: { content: Content, allowUpload?: boolean }) => {
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [file, setFile] = useState<File | null>(null);

    const uploadShown = allowUpload ?? false;

    const handleFileUpload = (event: { preventDefault: () => void; }) => {
        event.preventDefault();
        setIsSubmitting(true);
        const formData = new FormData();
        formData.append('file', file!);
        fetch(buildUrl('/upload'), {
            method: 'POST',
            body: formData,
        }).then(() => {
            window.location.reload();
        }).catch((error) => { setIsSubmitting(false); console.error('Error from upload:', error); alert((`Error: ${error}. Please adjust your request and try again.`)); });
    };

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
                            (<form id="fileUploadForm" onSubmit={handleFileUpload}>
                                <div className="flex flex-row justify-between content-center items-center">
                                    <input className="w-96 hover:cursor-pointer" type="file" onChange={(e) => setFile(e.target.files![0])} />
                                    <SubmitButton disabled={!file} text="Upload" />
                                </div>
                            </form>)}
                    </div>
                </div>
            </LightBorderedDiv>
        </>
    );
};
