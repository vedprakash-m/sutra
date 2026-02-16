/**
 * PromptsListPage - List and manage all prompts
 * Provides search, filter, and navigation to prompt builder/editor
 */
import React, { useState, useEffect, useCallback, useMemo } from "react";
import { Link, useNavigate } from "react-router-dom";
import { promptsApi } from "@/services/api";
import {
  PlusIcon,
  MagnifyingGlassIcon,
  PencilSquareIcon,
  TrashIcon,
  PlayIcon,
} from "@heroicons/react/24/outline";

interface Prompt {
  id: string;
  title: string;
  description: string;
  content: string;
  tags?: string[];
  collectionId?: string;
  createdAt?: string;
  updatedAt?: string;
}

export default function PromptsListPage() {
  const navigate = useNavigate();
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const loadPrompts = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await promptsApi.list({
        page: currentPage,
        limit: 20,
        search: searchQuery || undefined,
      });
      setPrompts((response as any)?.items || []);
      setTotalPages(
        Math.ceil(((response as any)?.pagination?.totalCount || 0) / 20) || 1,
      );
    } catch (error) {
      console.error("Error loading prompts:", error);
      setPrompts([]);
    } finally {
      setIsLoading(false);
    }
  }, [currentPage, searchQuery]);

  useEffect(() => {
    loadPrompts();
  }, [loadPrompts]);

  const handleDelete = async (id: string) => {
    if (!window.confirm("Are you sure you want to delete this prompt?")) return;
    try {
      await promptsApi.delete(id);
      setPrompts((prev) => prev.filter((p) => p.id !== id));
    } catch (error) {
      console.error("Error deleting prompt:", error);
    }
  };

  const filteredPrompts = useMemo(() => {
    if (!searchQuery) return prompts;
    const q = searchQuery.toLowerCase();
    return prompts.filter(
      (p) =>
        p.title?.toLowerCase().includes(q) ||
        p.description?.toLowerCase().includes(q) ||
        p.tags?.some((t: string) => t.toLowerCase().includes(q)),
    );
  }, [prompts, searchQuery]);

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Prompts</h1>
          <p className="text-sm text-gray-500 mt-1">
            Manage your prompt library
          </p>
        </div>
        <Link
          to="/prompts/new"
          className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
        >
          <PlusIcon className="h-4 w-4" />
          New Prompt
        </Link>
      </div>

      {/* Search */}
      <div className="relative mb-6">
        <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
        <input
          type="text"
          placeholder="Search prompts..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
        />
      </div>

      {/* List */}
      {isLoading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto" />
          <p className="text-gray-500 mt-3">Loading prompts...</p>
        </div>
      ) : filteredPrompts.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
          <p className="text-gray-500">
            {searchQuery ? "No prompts match your search." : "No prompts yet."}
          </p>
          <Link
            to="/prompts/new"
            className="inline-flex items-center gap-2 mt-4 text-indigo-600 hover:text-indigo-700"
          >
            <PlusIcon className="h-4 w-4" />
            Create your first prompt
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredPrompts.map((prompt) => (
            <div
              key={prompt.id}
              className="bg-white rounded-lg border border-gray-200 p-4 hover:border-indigo-300 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <Link
                    to={`/prompts/${prompt.id}`}
                    className="text-lg font-medium text-gray-900 hover:text-indigo-600"
                  >
                    {prompt.title}
                  </Link>
                  {prompt.description && (
                    <p className="text-sm text-gray-500 mt-1 line-clamp-2">
                      {prompt.description}
                    </p>
                  )}
                  {prompt.tags && prompt.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {prompt.tags.map((tag: string) => (
                        <span
                          key={tag}
                          className="px-2 py-0.5 text-xs rounded-full bg-gray-100 text-gray-600"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-2 ml-4">
                  <button
                    onClick={() => navigate(`/prompts/${prompt.id}`)}
                    className="p-2 text-gray-400 hover:text-indigo-600 rounded-lg hover:bg-gray-50"
                    title="Edit"
                  >
                    <PencilSquareIcon className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(prompt.id)}
                    className="p-2 text-gray-400 hover:text-red-600 rounded-lg hover:bg-gray-50"
                    title="Delete"
                  >
                    <TrashIcon className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2 mt-6">
          <button
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            className="px-3 py-1 rounded border border-gray-300 text-sm disabled:opacity-50"
          >
            Previous
          </button>
          <span className="px-3 py-1 text-sm text-gray-600">
            Page {currentPage} of {totalPages}
          </span>
          <button
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
            className="px-3 py-1 rounded border border-gray-300 text-sm disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
