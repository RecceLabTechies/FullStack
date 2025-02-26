"use client";

import { fetchDbStructure } from "@/api/dbApi";
import { UploadButton } from "@/app/dashboard/database_helper/UploadButton";
import { AdCampaignData } from "@/types/adCampaignTypes";
import React from "react";

export default function DatabaseHelper() {
  const [dbStructure, setDbStructure] = React.useState<AdCampaignData[]>();
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  React.useEffect(() => {
    const loadDbStructure = async () => {
      setIsLoading(true);
      setError(null);
      const data = await fetchDbStructure();
      if (data) {
        setDbStructure(data);
      } else {
        setError("Failed to fetch database structure");
      }
      setIsLoading(false);
    };
    loadDbStructure();
  }, []);

  return (
    <div>
      {dbStructure && <p>Database structure loaded successfully!</p>}
      {error && <p>{error}</p>}
      {isLoading && <p>Loading...</p>}
      {dbStructure && (
        <div className="mt-8 w-full overflow-x-auto">
          {Object.keys(dbStructure).map((dbName) => (
            <div key={dbName} className="mb-8 border border-gray-300 p-4">
              <h2 className="text-2xl font-bold text-white">{dbName}</h2>
              {Object.keys(
                dbStructure[dbName as keyof AdCampaignData] as Record<
                  string,
                  any
                >,
              ).map((collectionName) => (
                <div key={collectionName} className="mt-4">
                  <h3 className="text-xl font-semibold text-white">
                    Collection: {collectionName}
                  </h3>
                  {typeof (
                    dbStructure[dbName as keyof AdCampaignData] as Record<
                      string,
                      any
                    >
                  )[collectionName] === "string" ? (
                    <p className="text-gray-300">
                      {
                        (
                          dbStructure[dbName as keyof AdCampaignData] as Record<
                            string,
                            any
                          >
                        )[collectionName]
                      }
                    </p>
                  ) : (
                    <table className="min-w-full border-collapse bg-white text-black">
                      <thead>
                        <tr>
                          {Object.keys(
                            (
                              dbStructure[
                                dbName as keyof AdCampaignData
                              ] as Record<string, any>
                            )[collectionName][0] ?? {},
                          ).map((key) => (
                            <th key={key} className="border p-2">
                              {key}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {(
                          dbStructure[dbName as keyof AdCampaignData] as Record<
                            string,
                            any
                          >
                        )[collectionName].map((doc: any, index: number) => (
                          <tr key={index}>
                            {Object.keys(doc).map((key) => (
                              <td key={key} className="border p-2">
                                {JSON.stringify(doc[key])}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              ))}
            </div>
          ))}
        </div>
      )}
      <UploadButton />
    </div>
  );
}
