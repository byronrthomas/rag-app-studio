import { useState } from "react";
import { IsLoadingContext } from "./IsLoadingContext";
import { SpinnerOverlay } from "./SpinnerOverlay";

// @ts-expect-error children-can-be-anything
export const LoadingOverlayProvider = ({ children }) => {
    const [isLoading, setIsLoading] = useState(false);
    return (
        <IsLoadingContext.Provider value={(v) => setIsLoading(v)}>
            <SpinnerOverlay isVisible={isLoading} />
            {children}
        </IsLoadingContext.Provider>
    );
}

