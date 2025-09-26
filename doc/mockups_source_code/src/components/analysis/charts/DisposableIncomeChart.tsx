import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const mockData = [
  { month: 'Jan', '0 enfants': 850, '1-2 enfants': 1200, '3+ enfants': 1500 },
  { month: 'Fév', '0 enfants': 870, '1-2 enfants': 1250, '3+ enfants': 1550 },
  { month: 'Mar', '0 enfants': 900, '1-2 enfants': 1300, '3+ enfants': 1600 },
  { month: 'Avr', '0 enfants': 880, '1-2 enfants': 1280, '3+ enfants': 1580 },
  { month: 'Mai', '0 enfants': 920, '1-2 enfants': 1320, '3+ enfants': 1620 },
  { month: 'Jun', '0 enfants': 950, '1-2 enfants': 1350, '3+ enfants': 1650 }
];

const DisposableIncomeChart: React.FC = () => {
  return (
    <div className="bg-white p-6 rounded-lg shadow-sm">
      <h2 className="text-lg font-semibold mb-4">Évolution du Reste à Vivre par Bénéficiaire</h2>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={mockData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis tickFormatter={(value) => `${value}€`} />
            <Tooltip formatter={(value) => `${value}€`} />
            <Legend />
            <Bar dataKey="0 enfants" fill="#4F46E5" />
            <Bar dataKey="1-2 enfants" fill="#10B981" />
            <Bar dataKey="3+ enfants" fill="#F59E0B" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default DisposableIncomeChart;