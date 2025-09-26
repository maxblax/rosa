import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { BarChart2 } from 'lucide-react';

const data = [
  { month: 'Jan', beneficiaires: 65 },
  { month: 'Fév', beneficiaires: 72 },
  { month: 'Mar', beneficiaires: 85 },
  { month: 'Avr', beneficiaires: 78 },
  { month: 'Mai', beneficiaires: 90 },
  { month: 'Jun', beneficiaires: 95 }
];

const RecentChart: React.FC = () => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-800">Évolution des Bénéficiaires</h2>
        <BarChart2 className="text-green-600" />
      </div>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="beneficiaires" fill="#4F46E5" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default RecentChart;