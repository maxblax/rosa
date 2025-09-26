import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const mockData = [
  { month: 'Jan', beneficiaires: 156 },
  { month: 'Fév', beneficiaires: 165 },
  { month: 'Mar', beneficiaires: 172 },
  { month: 'Avr', beneficiaires: 180 },
  { month: 'Mai', beneficiaires: 185 },
  { month: 'Jun', beneficiaires: 190 }
];

const BeneficiaryCountChart: React.FC = () => {
  return (
    <div className="bg-white p-6 rounded-lg shadow-sm">
      <h2 className="text-lg font-semibold mb-4">Nombre de Bénéficiaires par Mois</h2>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={mockData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="beneficiaires" 
              stroke="#4F46E5" 
              strokeWidth={2}
              dot={{ fill: '#4F46E5' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default BeneficiaryCountChart;