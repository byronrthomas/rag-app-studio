import { useState } from 'react';
import chevLUrl from './assets/chevron_left.svg';
import chevRUrl from './assets/chevron_right.svg';
import { FileInfo } from '@common/types';

const PaginationControls = ({ count, page, handleChangePage, rowsPerPage }: { count: number, page: number, handleChangePage: (newPage: number) => void, rowsPerPage: number }) => {
    const numPages = Math.ceil(count / rowsPerPage);
    const currentPageText = `${page * rowsPerPage + 1}-${Math.min((page + 1) * rowsPerPage, count)} of ${count}`;
    return (
        <td>
            <div className='flex flex-row content-center justify-center'>
                <button className="bg-gray-panel-bg disabled:bg-whitesmoke" onClick={() => handleChangePage(Math.max(0, page - 1))} disabled={page === 0}>
                    <img src={chevLUrl} alt='Prev' /></button>
                <span className="mx-1">{currentPageText}</span>
                <button className="bg-gray-panel-bg disabled:bg-whitesmoke" onClick={() => handleChangePage(Math.min(numPages - 1, page + 1))} disabled={page === numPages - 1}><img src={chevRUrl} alt='Next'></img> </button>
            </div>
        </td>
    );
}

export const FileTable = ({ files }: { files: FileInfo[] }) => {
    const [page, setPage] = useState(0);
    const handleChangePage = (newPage: number) => {
        setPage(newPage);
    };
    const rowsPerPage = 10;
    // Sort the files before we slice into pages
    const all_files = [...files];
    all_files.sort((a, b) => a.file_name.localeCompare(b.file_name));
    const currentPage = files.slice(page * rowsPerPage, (page + 1) * rowsPerPage);
    return (
        <table className="w-full table-auto border-collapse border border-gray-med bg-whitesmoke">
            <thead>
                <tr>
                    <th className="border border-gray-med bg-gray-med">Filename</th>
                    <th className="border border-gray-med bg-gray-med">Nodes</th>
                </tr>
            </thead>
            <tbody>
                {currentPage.map((file, i) => {
                    return (
                        <tr key={i}>
                            <td className="border border-gray-med">{file.file_name}</td>
                            <td className="border border-gray-med">{file.node_count}</td>
                        </tr>
                    );
                })}
            </tbody>
            <tfoot>
                <tr>
                    <PaginationControls count={files.length} page={page} handleChangePage={handleChangePage} rowsPerPage={rowsPerPage} />
                </tr>
            </tfoot>
        </table>
    );
}