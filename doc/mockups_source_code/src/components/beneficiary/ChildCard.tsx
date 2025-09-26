import React from 'react';

interface ChildProps {
  name: string;
  firstName: string;
  age: number;
  observation: string;
  onObservationChange: (observation: string) => void;
  isEditing: boolean;
}

const ChildCard: React.FC<ChildProps> = ({
  name,
  firstName,
  age,
  observation,
  onObservationChange,
  isEditing
}) => {
  return (
    <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
      <div className="space-y-2">
        <div className="flex justify-between">
          <h3 className="font-medium text-gray-900">{firstName} {name}</h3>
          <span className="text-sm text-gray-500">{age} ans</span>
        </div>
        <div>
          <label htmlFor="observation" className="block text-sm font-medium text-gray-700 mb-1">
            Observations
          </label>
          {isEditing ? (
            <textarea
              id="observation"
              value={observation}
              onChange={(e) => onObservationChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-sm"
              rows={2}
            />
          ) : (
            <p className="text-sm text-gray-600">{observation || 'Aucune observation'}</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChildCard;