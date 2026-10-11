import React from 'react';
import { ArrowDownRight, ArrowUpRight } from 'lucide-react';

interface Transaction {
  id: string;
  date: string;
  amount: number;
  merchant: string;
  type: string;
}

interface TransactionsTableProps {
  transactions: Transaction[];
}

export const TransactionsTable: React.FC<TransactionsTableProps> = ({ transactions }) => {
  if (!transactions || transactions.length === 0) return null;

  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-hidden my-4 max-w-2xl shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="bg-slate-50 text-slate-500 font-medium">
            <tr>
              <th className="px-4 py-3">Date</th>
              <th className="px-4 py-3">Merchant</th>
              <th className="px-4 py-3 text-right">Amount</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {transactions.map((tx) => (
              <tr key={tx.id} className="hover:bg-slate-50 transition-colors">
                <td className="px-4 py-3 text-slate-500 whitespace-nowrap">
                  {new Date(tx.date).toLocaleDateString()}
                </td>
                <td className="px-4 py-3 font-medium text-slate-900">
                  {tx.merchant}
                </td>
                <td className="px-4 py-3 text-right whitespace-nowrap">
                  <div className="flex items-center justify-end gap-1">
                    {tx.amount < 0 ? (
                      <ArrowUpRight size={14} className="text-slate-400" />
                    ) : (
                      <ArrowDownRight size={14} className="text-green-500" />
                    )}
                    <span className={tx.amount < 0 ? 'text-slate-900' : 'text-green-600'}>
                      ₹ {Math.abs(tx.amount).toFixed(2)}
                    </span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
