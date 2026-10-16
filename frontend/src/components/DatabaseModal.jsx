import React, { useState, useEffect } from 'react';
import {
  Database,
  Table,
  Search,
  RefreshCw,
  X,
  ChevronLeft,
  ChevronRight,
  Plus,
  Trash2,
  Edit2,
  Eye,
  RotateCcw,
  CheckCircle2,
  AlertCircle,
  FileSpreadsheet
} from 'lucide-react';
import {
  fetchDatabaseOverview,
  fetchDatabaseTables,
  fetchTableData,
  insertTableRow,
  updateTableRow,
  deleteTableRow,
  resetDatabase
} from '../services/api';

export default function DatabaseModal({ isOpen, onClose }) {
  const [overview, setOverview] = useState(null);
  const [tables, setTables] = useState([]);
  const [selectedTable, setSelectedTable] = useState('');
  const [tableSearch, setTableSearch] = useState('');
  
  // Table Data State
  const [tableData, setTableData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dataSearch, setDataSearch] = useState('');
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(25);
  
  // Modals for Single Record
  const [inspectRecord, setInspectRecord] = useState(null);
  const [editRecord, setEditRecord] = useState(null);
  const [isInserting, setIsInserting] = useState(false);
  const [editFormData, setEditFormData] = useState({});

  // Status message
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const loadTables = async () => {
    try {
      setLoading(true);
      const [ovData, tblData] = await Promise.all([
        fetchDatabaseOverview(),
        fetchDatabaseTables()
      ]);
      setOverview(ovData);
      setTables(tblData);
      if (!selectedTable && tblData.length > 0) {
        setSelectedTable(tblData[0].table_name);
      }
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadTableRows = async () => {
    if (!selectedTable) return;
    try {
      setLoading(true);
      const data = await fetchTableData(selectedTable, {
        page,
        limit,
        search: dataSearch
      });
      setTableData(data);
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadTables();
    }
  }, [isOpen]);

  useEffect(() => {
    if (isOpen && selectedTable) {
      setPage(1);
      loadTableRows();
    }
  }, [selectedTable, dataSearch, limit]);

  useEffect(() => {
    if (isOpen && selectedTable) {
      loadTableRows();
    }
  }, [page]);

  if (!isOpen) return null;

  const filteredTables = tables.filter(t => 
    t.table_name.toLowerCase().includes(tableSearch.toLowerCase())
  );

  const currentTableMeta = tables.find(t => t.table_name === selectedTable);

  const handleResetDb = async () => {
    if (!window.confirm("Are you sure you want to restore the entire SQLite database to the original JSON file? Any manual edits will be reset.")) return;
    try {
      setLoading(true);
      const res = await resetDatabase();
      showToast(res.message);
      await loadTables();
      await loadTableRows();
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm(`Delete record #${id} from ${selectedTable}?`)) return;
    try {
      await deleteTableRow(selectedTable, id);
      showToast(`Record #${id} deleted.`);
      loadTableRows();
      loadTables();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleOpenEdit = (row) => {
    setEditRecord(row);
    setEditFormData({ ...row });
  };

  const handleOpenInsert = () => {
    if (!currentTableMeta) return;
    const initial = {};
    currentTableMeta.columns.forEach(c => {
      if (c.name !== 'id') initial[c.name] = '';
    });
    setEditFormData(initial);
    setIsInserting(true);
  };

  const handleSaveEdit = async () => {
    try {
      if (isInserting) {
        await insertTableRow(selectedTable, editFormData);
        showToast(`New record inserted into ${selectedTable}!`);
      } else {
        await updateTableRow(selectedTable, editRecord.id, editFormData);
        showToast(`Record #${editRecord.id} updated successfully!`);
      }
      setIsInserting(false);
      setEditRecord(null);
      loadTableRows();
      loadTables();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/50 backdrop-blur-xs p-4 sm:p-6 animate-fadeIn">
      <div className="relative w-full h-[94vh] max-w-7xl bg-white border border-gray-200 rounded-xl shadow-2xl flex flex-col overflow-hidden">
        
        {/* Toast Alert */}
        {toast && (
          <div className={`absolute top-4 right-16 z-50 flex items-center gap-2 px-4 py-2 rounded-lg border text-xs font-semibold shadow-md transition-all ${
            toast.type === 'error'
              ? 'bg-red-50 border-red-200 text-red-700'
              : 'bg-emerald-50 border-emerald-200 text-emerald-700'
          }`}>
            {toast.type === 'error' ? <AlertCircle className="w-4 h-4 text-red-600" /> : <CheckCircle2 className="w-4 h-4 text-emerald-600" />}
            {toast.message}
          </div>
        )}

        {/* Modal Top Header with Postman Orange accents */}
        <div className="flex items-center justify-between px-6 py-3.5 border-b border-gray-200 bg-white">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-orange-50 border border-orange-200 flex items-center justify-center text-[#FF6C37]">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h2 className="text-base font-bold text-gray-900 tracking-tight">University SQLite Database State</h2>
                <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-gray-100 text-gray-700 border border-gray-200">
                  SQLite 3
                </span>
                <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-orange-50 text-[#FF6C37] border border-orange-200 font-mono">
                  Live Persistent
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-0.5">
                {overview ? `${overview.total_tables} Tables • ${overview.total_records.toLocaleString()} Total Records • ${overview.file_size_mb} MB on disk` : 'Loading database statistics...'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              onClick={() => { loadTables(); loadTableRows(); }}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium bg-white hover:bg-gray-50 text-gray-700 transition-colors border border-gray-300 shadow-2xs"
              title="Refresh database state"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-gray-500 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>

            <button
              onClick={handleResetDb}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold bg-orange-50 hover:bg-orange-100 text-[#FF6C37] transition-colors border border-orange-200 shadow-2xs"
              title="Re-populate pristine JSON into database"
            >
              <RotateCcw className="w-3.5 h-3.5 text-[#FF6C37]" />
              Reset to JSON
            </button>

            <button
              onClick={onClose}
              className="p-1.5 rounded-md text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors ml-2"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Main Content (Split Sidebar & Data View) */}
        <div className="flex flex-1 overflow-hidden">
          
          {/* Left Sidebar: 30 Tables List (Postman Collections style) */}
          <div className="w-72 border-r border-gray-200 bg-[#F9FAFB] flex flex-col">
            <div className="p-3 border-b border-gray-200 bg-white">
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Filter 30 tables..."
                  value={tableSearch}
                  onChange={(e) => setTableSearch(e.target.value)}
                  className="w-full pl-8 pr-3 py-1.5 text-xs bg-white border border-gray-300 rounded-md text-gray-800 placeholder-gray-400 focus:outline-none focus:border-[#FF6C37] focus:ring-1 focus:ring-[#FF6C37]"
                />
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
              {filteredTables.map(t => {
                const isSelected = selectedTable === t.table_name;
                return (
                  <button
                    key={t.table_name}
                    onClick={() => setSelectedTable(t.table_name)}
                    className={`w-full flex items-center justify-between px-3 py-2 rounded-md text-left text-xs transition-colors ${
                      isSelected
                        ? 'bg-orange-50 text-[#FF6C37] font-semibold border-l-3 border-[#FF6C37]'
                        : 'text-gray-700 hover:text-gray-900 hover:bg-gray-200/50'
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      <Table className={`w-3.5 h-3.5 shrink-0 ${isSelected ? 'text-[#FF6C37]' : 'text-gray-400'}`} />
                      <span className="truncate">{t.table_name}</span>
                    </div>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono shrink-0 border ${
                      isSelected
                        ? 'bg-orange-100/80 text-[#FF6C37] border-orange-200'
                        : 'bg-white text-gray-500 border-gray-200'
                    }`}>
                      {t.row_count}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Right Main Table Area */}
          <div className="flex-1 flex flex-col bg-white overflow-hidden">
            
            {/* Table Control Bar */}
            <div className="px-6 py-2.5 border-b border-gray-200 flex flex-wrap items-center justify-between gap-4 bg-white">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <FileSpreadsheet className="w-4 h-4 text-[#FF6C37]" />
                  <span className="text-sm font-bold text-gray-900 tracking-wide">{selectedTable}</span>
                </div>
                {tableData && (
                  <span className="text-xs text-gray-600 font-mono bg-gray-100 px-2.5 py-0.5 rounded-full border border-gray-200">
                    {tableData.total_rows.toLocaleString()} entries ({currentTableMeta?.columns?.length || 0} columns)
                  </span>
                )}
              </div>

              <div className="flex items-center gap-3">
                <div className="relative">
                  <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input
                    type="text"
                    placeholder={`Search in ${selectedTable}...`}
                    value={dataSearch}
                    onChange={(e) => setDataSearch(e.target.value)}
                    className="w-56 pl-8 pr-3 py-1.5 text-xs bg-white border border-gray-300 rounded-md text-gray-800 placeholder-gray-400 focus:outline-none focus:border-[#FF6C37] focus:ring-1 focus:ring-[#FF6C37]"
                  />
                </div>

                <button
                  onClick={handleOpenInsert}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold bg-[#FF6C37] hover:bg-[#E85B27] text-white transition-colors shadow-2xs"
                >
                  <Plus className="w-3.5 h-3.5" />
                  Insert Row
                </button>
              </div>
            </div>

            {/* Table View */}
            <div className="flex-1 overflow-auto bg-white">
              {loading && !tableData ? (
                <div className="flex items-center justify-center h-full text-gray-500 text-xs gap-2">
                  <RefreshCw className="w-4 h-4 animate-spin text-[#FF6C37]" />
                  Fetching records from SQLite...
                </div>
              ) : tableData && tableData.rows && tableData.rows.length > 0 ? (
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="sticky top-0 bg-gray-50 border-b border-gray-200 z-10 text-gray-600 font-mono">
                    <tr>
                      <th className="py-2.5 px-3 text-center w-24">Actions</th>
                      {tableData.columns.map(c => (
                        <th key={c} className="py-2.5 px-4 font-semibold text-gray-700 whitespace-nowrap">
                          {c}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 font-sans">
                    {tableData.rows.map((row, idx) => (
                      <tr key={row.id || idx} className="hover:bg-orange-50/30 transition-colors group">
                        <td className="py-2 px-3 text-center whitespace-nowrap">
                          <div className="flex items-center justify-center gap-1 opacity-70 group-hover:opacity-100">
                            <button
                              onClick={() => setInspectRecord(row)}
                              title="Inspect JSON"
                              className="p-1 text-gray-500 hover:text-[#FF6C37] hover:bg-gray-100 rounded transition-colors"
                            >
                              <Eye className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={() => handleOpenEdit(row)}
                              title="Edit Row"
                              className="p-1 text-gray-500 hover:text-amber-600 hover:bg-gray-100 rounded transition-colors"
                            >
                              <Edit2 className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={() => handleDelete(row.id)}
                              title="Delete Row"
                              className="p-1 text-gray-500 hover:text-red-600 hover:bg-gray-100 rounded transition-colors"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </td>
                        {tableData.columns.map(c => {
                          const val = row[c];
                          const isNull = val === null || val === undefined;
                          return (
                            <td key={c} className="py-2 px-4 whitespace-nowrap text-gray-800 font-mono text-[11px]">
                              {isNull ? (
                                <span className="text-gray-400 italic">NULL</span>
                              ) : typeof val === 'number' ? (
                                <span className="text-[#FF6C37] font-semibold">{val}</span>
                              ) : (
                                <span>{String(val)}</span>
                              )}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-gray-400 text-xs">
                  <Database className="w-8 h-8 text-gray-300 mb-2" />
                  <p>No records found in this table matching your query.</p>
                </div>
              )}
            </div>

            {/* Pagination Bottom Bar */}
            {tableData && (
              <div className="px-6 py-2.5 border-t border-gray-200 bg-white flex items-center justify-between text-xs text-gray-600">
                <div className="flex items-center gap-2">
                  <span>Rows per page:</span>
                  <select
                    value={limit}
                    onChange={(e) => setLimit(Number(e.target.value))}
                    className="bg-white border border-gray-300 rounded px-2 py-1 text-gray-800 focus:outline-none focus:border-[#FF6C37] font-mono"
                  >
                    <option value={10}>10</option>
                    <option value={25}>25</option>
                    <option value={50}>50</option>
                    <option value={100}>100</option>
                  </select>
                  <span className="ml-3 text-gray-500">
                    Showing {((page - 1) * limit) + 1} - {Math.min(page * limit, tableData.total_rows)} of {tableData.total_rows}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page <= 1}
                    className="p-1.5 rounded border border-gray-300 bg-white text-gray-700 disabled:opacity-40 hover:bg-gray-50"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <span className="px-2 font-mono text-gray-800 font-medium">
                    Page {page} of {tableData.total_pages || 1}
                  </span>
                  <button
                    onClick={() => setPage(p => Math.min(tableData.total_pages, p + 1))}
                    disabled={page >= tableData.total_pages}
                    className="p-1.5 rounded border border-gray-300 bg-white text-gray-700 disabled:opacity-40 hover:bg-gray-50"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* View Record JSON Modal */}
        {inspectRecord && (
          <div className="fixed inset-0 z-60 flex items-center justify-center bg-gray-900/40 p-4">
            <div className="w-full max-w-lg bg-white border border-gray-200 rounded-xl p-5 shadow-2xl flex flex-col">
              <div className="flex items-center justify-between pb-3 border-b border-gray-200">
                <h3 className="text-sm font-bold text-gray-900">Record Details (JSON)</h3>
                <button onClick={() => setInspectRecord(null)} className="text-gray-400 hover:text-gray-700">
                  <X className="w-4 h-4" />
                </button>
              </div>
              <pre className="mt-3 p-3 bg-gray-50 rounded-lg border border-gray-200 text-gray-900 font-mono text-xs overflow-auto max-h-96">
                {JSON.stringify(inspectRecord, null, 2)}
              </pre>
            </div>
          </div>
        )}

        {/* Edit / Insert Record Modal */}
        {(editRecord || isInserting) && (
          <div className="fixed inset-0 z-60 flex items-center justify-center bg-gray-900/40 p-4">
            <div className="w-full max-w-md bg-white border border-gray-200 rounded-xl p-5 shadow-2xl flex flex-col">
              <div className="flex items-center justify-between pb-3 border-b border-gray-200">
                <h3 className="text-sm font-bold text-gray-900">
                  {isInserting ? `Insert Record into ${selectedTable}` : `Edit ${selectedTable} #${editRecord.id}`}
                </h3>
                <button
                  onClick={() => { setEditRecord(null); setIsInserting(false); }}
                  className="text-gray-400 hover:text-gray-700"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="mt-3 max-h-96 overflow-y-auto space-y-3 pr-1">
                {currentTableMeta?.columns?.map(col => {
                  if (col.name === 'id' && isInserting) return null;
                  const isPk = col.name === 'id';
                  return (
                    <div key={col.name}>
                      <label className="block text-[11px] font-mono text-gray-600 mb-1">
                        {col.name} <span className="text-gray-400">({col.type})</span>
                      </label>
                      <input
                        type="text"
                        disabled={isPk}
                        value={editFormData[col.name] ?? ''}
                        onChange={(e) => setEditFormData({ ...editFormData, [col.name]: e.target.value })}
                        className="w-full px-3 py-1.5 text-xs bg-white border border-gray-300 rounded-md text-gray-900 focus:outline-none focus:border-[#FF6C37] focus:ring-1 focus:ring-[#FF6C37] disabled:bg-gray-100 disabled:text-gray-400"
                      />
                    </div>
                  );
                })}
              </div>

              <div className="mt-4 pt-3 border-t border-gray-200 flex justify-end gap-2">
                <button
                  onClick={() => { setEditRecord(null); setIsInserting(false); }}
                  className="px-3 py-1.5 rounded-md text-xs font-medium text-gray-600 hover:bg-gray-100"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveEdit}
                  className="px-4 py-1.5 rounded-md text-xs font-semibold bg-[#FF6C37] hover:bg-[#E85B27] text-white shadow-2xs"
                >
                  {isInserting ? 'Save Record' : 'Apply Changes'}
                </button>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
