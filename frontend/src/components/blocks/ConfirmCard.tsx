import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { confirmAction, cancelAction } from '../../api/client';
import { Check, X, ShieldAlert } from 'lucide-react';

interface ConfirmCardProps {
  actionId: string;
  type: string;
  details: Record<string, unknown>;
  onResolved: (status: 'confirmed' | 'cancelled') => void;
}

export const ConfirmCard: React.FC<ConfirmCardProps> = ({ actionId, type, details, onResolved }) => {
  const { token } = useAuth();
  const [isProcessing, setIsProcessing] = React.useState(false);
  const [resolvedStatus, setResolvedStatus] = React.useState<'pending' | 'confirmed' | 'cancelled'>('pending');

  const handleConfirm = async () => {
    if (!token) return;
    setIsProcessing(true);
    try {
      await confirmAction(actionId, token);
      setResolvedStatus('confirmed');
      onResolved('confirmed');
    } catch (e) {
      console.error(e);
      alert('Failed to confirm action');
      setIsProcessing(false);
    }
  };

  const handleCancel = async () => {
    if (!token) return;
    setIsProcessing(true);
    try {
      await cancelAction(actionId, token);
      setResolvedStatus('cancelled');
      onResolved('cancelled');
    } catch (e) {
      console.error(e);
      alert('Failed to cancel action');
      setIsProcessing(false);
    }
  };

  if (resolvedStatus === 'confirmed') {
    return (
      <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl p-4 my-3 text-sm flex items-center gap-2">
        <Check size={18} className="text-emerald-600" />
        <span className="font-medium">Action Confirmed & Executed Successfully</span>
      </div>
    );
  }

  if (resolvedStatus === 'cancelled') {
    return (
      <div className="bg-slate-50 border border-slate-200 text-slate-600 rounded-xl p-4 my-3 text-sm flex items-center gap-2">
        <X size={18} className="text-slate-400" />
        <span className="font-medium">Action Cancelled</span>
      </div>
    );
  }

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm my-4 w-full max-w-md">
      <div className="flex items-center gap-2 mb-4 text-blue-600">
        <ShieldAlert size={20} />
        <h3 className="font-semibold text-slate-800">Action Required</h3>
      </div>
      
      <div className="bg-slate-50 p-4 rounded-lg mb-6 text-sm text-slate-700">
        <div className="font-medium mb-2 uppercase text-xs text-slate-500 tracking-wider">
          {type.replace('_', ' ')}
        </div>
        <div className="space-y-1">
          {Object.entries(details).map(([k, v]) => (
            <div key={k} className="flex justify-between">
              <span className="text-slate-500">{k}:</span>
              <span className="font-medium text-slate-900">{String(v)}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="flex gap-3">
        <button
          onClick={handleCancel}
          disabled={isProcessing}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-white border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors disabled:opacity-50"
        >
          <X size={16} /> Cancel
        </button>
        <button
          onClick={handleConfirm}
          disabled={isProcessing}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          <Check size={16} /> Confirm
        </button>
      </div>
    </div>
  );
};
