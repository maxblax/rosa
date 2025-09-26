import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const mockData = [
  { month: 'Jan', nouveaux: 12 },
  { month: 'Fév', nouveaux: 15 },
  { month: 'Mar', nouveaux: 10 },
  { month: 'Avr', nouveaux: 18 },
  { month: 'Mai', nouveaux: 14 },
  { month: 'Jun', nouveaux: 16 }
];

const NewBeneficiariesChart: React.FC = () => {
  return (
    <div className="bg-white p-6 rounded-lg shadow-sm">
      <h2 className="text-lg font-semibold mb-4">Nouveaux Arrivants Bénéficiaires par Mois</h2>
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
              dataKey="nouveaux" 
              stroke="#EC4899" 
              strokeWidth={2}
              dot={{ fill: '#EC4899' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default NewBeneficiariesChart;