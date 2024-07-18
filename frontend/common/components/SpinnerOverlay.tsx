import svgUrl from './assets/cycle_light_gray.svg';

export const SpinnerOverlay = ({ isVisible }: { isVisible: boolean }) => {
    if (!isVisible) return null;

    return (
        <div className="fixed top-0 left-0 w-full h-full bg-gray-dark bg-opacity-50 flex justify-center items-center z-50">
            <div className='bg-gray-dark/75 p-8 flex flex-col'>
                <div className="flex flex-row items-center">
                    <div className="text-white text-whitesmoke text-2xl">Loading...</div>
                    <img src={svgUrl} alt="spinner" className="animate-spin w-20 h-20" />
                </div>
                <div className="text-white text-whitesmoke text-sm font-semibold">Please do not refresh the page, it will automatically update. Changing the model takes several minutes.</div>
            </div>


        </div>
    );
};