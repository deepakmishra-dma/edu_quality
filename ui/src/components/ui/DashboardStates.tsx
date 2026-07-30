import { Loader2 } from "lucide-react";

interface PanelStateProps {
  isLoading: boolean;
  error: Error | null;
  isEmpty?: boolean;
  emptyMessage?: string;
}

/**
 * Loading / error / empty placeholder shared by the admissions dashboard panels.
 * Returns null once there is data to show.
 */
const PanelState = ({
  isLoading,
  error,
  isEmpty = false,
  emptyMessage = "No data for this selection yet.",
}: PanelStateProps): JSX.Element | null => {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center gap-2 py-10 text-gray-500">
        <Loader2 className="h-4 w-4 animate-spin" />
        <span>Loading…</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-10 text-center text-red-600">
        Could not load this data. {error.message}
      </div>
    );
  }

  if (isEmpty) {
    return <div className="py-10 text-center text-gray-500">{emptyMessage}</div>;
  }

  return null;
};

export default PanelState;
