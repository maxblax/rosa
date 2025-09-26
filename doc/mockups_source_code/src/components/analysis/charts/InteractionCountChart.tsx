import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const mockData = [
  { month: 'Jan', interactions: 45 },
  { month: 'Fév', interactions: 52 },
  { month: 'Mar', interactions: 48 },
  { month: 'Avr', interactions: 58 },
  { month: 'Mai', interactions: 62 },
  { month: 'Jun', interactions: 55 }
];

const InteractionCountChart: React.FC = () => {
  return (
    <div className="bg-white p-6 rounded-lg shadow-sm">
      <h2 className="text-lg font-semibold mb-4">Nombre d'Interactions par Mois</h2>
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
              dataKey="interactions" 
              stroke="#10B981" 
              strokeWidth={2}
              dot={{ fill: '#10B981' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default InteractionCountChart;