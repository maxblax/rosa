import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const mockData = [
  { month: 'Jan', donations: 2500 },
  { month: 'Fév', donations: 3200 },
  { month: 'Mar', donations: 2800 },
  { month: 'Avr', donations: 3500 },
  { month: 'Mai', donations: 4200 },
  { month: 'Jun', donations: 3800 }
];

const DonationsChart: React.FC = () => {
  return (
    <div className="bg-white p-6 rounded-lg shadow-sm">
      <h2 className="text-lg font-semibold mb-4">Récolte de Donateurs (en €)</h2>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={mockData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis tickFormatter={(value) => `${value}€`} />
            <Tooltip formatter={(value) => `${value}€`} />
            <Legend />
            <Bar dataKey="donations" fill="#8B5CF6" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default DonationsChart;