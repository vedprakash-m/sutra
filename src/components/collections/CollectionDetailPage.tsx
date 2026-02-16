/**
 * CollectionDetailPage - View and manage a single collection
 * Shows collection metadata, contained prompts, and version history
 */
import React, { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { collectionsApi, promptsApi } from "@/services/api";
import {
  ArrowLeftIcon,
  PencilSquareIcon,
  TrashIcon,
  PlusIcon,
  DocumentTextIcon,
} from "@heroicons/react/24/outline";

interface Collection {
  id: string;
  name: string;
  description: string;
  type?: string;
  promptCount?: number;
  createdAt?: string;
  updatedAt?: string;
}

interface Prompt {
  id: string;
  title: string;
  description: string;
  tags?: string[];
}

export default function CollectionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [collection, setCollection] = useState<Collection | null>(null);
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");

  const loadCollection = useCallback(async () => {
    if (!id) return;
    setIsLoading(true);
    try {
      const data = await collectionsApi.get(id);
      setCollection(data as any);
      setEditName((data as any)?.name || "");
      setEditDescription((data as any)?.description || "");

      // Load prompts in this collection
      const promptsData = await promptsApi.list({ collection_id: id });
      setPrompts((promptsData as any)?.items || []);
    } catch (error) {
      console.error("Error loading collection:", error);
      navigate("/collections");
    } finally {
      setIsLoading(false);
    }
  }, [id, navigate]);

  useEffect(() => {
    loadCollection();
  }, [loadCollection]);

  const handleSave = async () => {
    if (!id || !collection) return;
    try {
      await collectionsApi.update(id, {
        name: editName,
        description: editDescription,
      } as any);
      setCollection((prev) =>
        prev ? { ...prev, name: editName, description: editDescription } : prev,
      );
      setIsEditing(false);
    } catch (error) {
      console.error("Error updating collection:", error);
    }
  };

  const handleDelete = async () => {
    if (!id) return;
    if (
      !window.confirm(
        "Are you sure you want to delete this collection? This cannot be undone.",
      )
    )
      return;
    try {
      await collectionsApi.delete(id);
      navigate("/collections");
    } catch (error) {
      console.error("Error deleting collection:", error);
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto" />
          <p className="text-gray-500 mt-3">Loading collection...</p>
        </div>
      </div>
    );
  }

  if (!collection) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <p className="text-gray-500">Collection not found.</p>
        <Link to="/collections" className="text-indigo-600 hover:text-indigo-700">
          Back to collections
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Back link */}
      <Link
        to="/collections"
        className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-6"
      >
        <ArrowLeftIcon className="h-4 w-4" />
        Back to Collections
      </Link>

      {/* Collection Header */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
        {isEditing ? (
          <div className="space-y-4">
            <input
              type="text"
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-xl font-bold focus:ring-2 focus:ring-indigo-500"
            />
            <textarea
              value={editDescription}
              onChange={(e) => setEditDescription(e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
            />
            <div className="flex gap-2">
              <button
                onClick={handleSave}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
              >
                Save
              </button>
              <button
                onClick={() => setIsEditing(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {collection.name}
              </h1>
              {collection.description && (
                <p className="text-gray-500 mt-2">{collection.description}</p>
              )}
              <div className="flex items-center gap-3 mt-3 text-sm text-gray-400">
                {collection.type && (
                  <span className="capitalize">{collection.type}</span>
                )}
                <span>{prompts.length} prompts</span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsEditing(true)}
                className="p-2 text-gray-400 hover:text-indigo-600 rounded-lg hover:bg-gray-50"
                title="Edit"
              >
                <PencilSquareIcon className="h-5 w-5" />
              </button>
              <button
                onClick={handleDelete}
                className="p-2 text-gray-400 hover:text-red-600 rounded-lg hover:bg-gray-50"
                title="Delete"
              >
                <TrashIcon className="h-5 w-5" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Prompts in Collection */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Prompts</h2>
          <Link
            to="/prompts/new"
            className="inline-flex items-center gap-1 text-sm text-indigo-600 hover:text-indigo-700"
          >
            <PlusIcon className="h-4 w-4" />
            Add Prompt
          </Link>
        </div>

        {prompts.length === 0 ? (
          <div className="text-center py-8 bg-white rounded-lg border border-gray-200">
            <DocumentTextIcon className="h-8 w-8 text-gray-400 mx-auto" />
            <p className="text-gray-500 mt-2">
              No prompts in this collection yet.
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {prompts.map((prompt) => (
              <Link
                key={prompt.id}
                to={`/prompts/${prompt.id}`}
                className="block bg-white rounded-lg border border-gray-200 p-4 hover:border-indigo-300 transition-colors"
              >
                <div className="font-medium text-gray-900">{prompt.title}</div>
                {prompt.description && (
                  <div className="text-sm text-gray-500 mt-1 line-clamp-1">
                    {prompt.description}
                  </div>
                )}
                {prompt.tags && prompt.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {prompt.tags.map((tag) => (
                      <span
                        key={tag}
                        className="px-2 py-0.5 text-xs rounded-full bg-gray-100 text-gray-600"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
