const puppeteer = require('puppeteer');
const axios = require('axios').default;
const fs = require('fs');

const TIMEOUT = 1;
const instance = axios.create({
    baseURL: 'https://comelec.gov.ph',
    headers: {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 12_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/69.0.3497.105 Mobile/15E148 Safari/605.1'
    }
});

async function getCitiesMunicipalities(province) {
    console.log(`Processing Province: ${province.rn}`);
    // await new Promise(resolve => setTimeout(resolve, TIMEOUT));
    var response = await instance.get(`/2019NLEResults/data/regions/${province.url}.json`);
    return response.data.srs;
}

async function getBarangays(cityMun) {
    console.log(`Processing City/Municipality: ${cityMun.rn}`);
    // await new Promise(resolve => setTimeout(resolve, TIMEOUT));
    var response = await instance.get(`/2019NLEResults/data/regions/${cityMun.url}.json`);
    return response.data.srs;
}

async function getPrecints(barangay) {
    console.log(`Processing Barangay: ${barangay.rn}`);
    // await new Promise(resolve => setTimeout(resolve, TIMEOUT));
    var response = await instance.get(`/2019NLEResults/data/regions/${barangay.url}.json`);
    return response.data.pps;
}

async function getVotes(precint) {
    try {
        console.log(`Fetching votes from Precint No. ${precint.ppcc} - ${precint.ppn}`);
        // await new Promise(resolve => setTimeout(resolve, TIMEOUT));
        var response = await instance.get(`/2019NLEResults/data/results/${precint.vbs[0].url}.json`);
        return response.data;
    } catch (error) {
        console.log(`Status Code: ${error.response.status}`);
        if (error.response.status === 404) {
            return [];
        }
    }
}

(async () => {
    var regionLink = '/2019NLEResults/data/regions/0/8.json'
    var lookup = JSON.parse(fs.readFileSync('./5567.json', 'utf8'));
    var output = [];
    var response = await instance.get('/2019NLEResults/data/regions/0/8.json');
    var provinces = response.data.srs;
    var x = 0;

    var proceed = false;

    for (const kProvince in provinces) {
        if (Object.hasOwnProperty.call(provinces, kProvince)) {
            const province = provinces[kProvince];
            var cityMuns = await getCitiesMunicipalities(province);

            for (const kCityMun in cityMuns) {
                if (Object.hasOwnProperty.call(cityMuns, kCityMun)) {
                    const cityMun = cityMuns[kCityMun];
                    const cityMunName = cityMun.rn;

                    // if (!proceed) {
                    //     if (cityMunName.includes(FILTER)) {
                    //         proceed = true;
                    //     }
                    // }

                    // if (!proceed)
                    //     continue;

                    var barangays = await getBarangays(cityMun);
                    for (const kBarangay in barangays) {
                        if (Object.hasOwnProperty.call(barangays, kBarangay)) {
                            const barangay = barangays[kBarangay];
                            var precints = await getPrecints(barangay);

                            for (const kPrecint in precints) {
                                if (Object.hasOwnProperty.call(precints, kPrecint)) {
                                    const precint = precints[kPrecint];
                                    var votesResponse = await getVotes(precint);
                                    if (!votesResponse || votesResponse.length === 0) {
                                        continue;
                                    }

                                    var votes = votesResponse.rs;

                                    var registeredInfo = votesResponse.cos.find(v => v.cn == 'expected-voters');
                                    var actualVotersInfo = votesResponse.cos.find(v => v.cn == 'number-of-voters-who-actually-voted');
                                    var processBallotsInfo = votesResponse.cos.find(v => v.cn == 'valid-votes');

                                    var registeredVoters = registeredInfo.ct;
                                    var actualVoters = actualVotersInfo.ct;
                                    var processBallots = processBallotsInfo.ct;

                                    var partyVotes = votes.filter((v) => v.cc === 5567);

                                    for (const kPartyVote in partyVotes) {
                                        if (Object.hasOwnProperty.call(partyVotes, kPartyVote)) {
                                            try {
                                                const partyVote = partyVotes[kPartyVote];
                                                var data = {
                                                    dProvince: province.rn,
                                                    dMunicipality: cityMun.rn,
                                                    dBarangay: barangay.rn,
                                                    dPrecint: precint.ppcc,
                                                    dPartyName: lookup.bos.find(l => l.boc === partyVote.bo).bon,
                                                    dVote: partyVote.v,
                                                    dTotal: partyVote.tot,
                                                    dPercentage: partyVote.per,
                                                    dRegistered: registeredVoters,
                                                    dProcessedBallots: processBallots,
                                                    dActualVoters: actualVoters
                                                }

                                                console.log(data);

                                                output.push(data);
                                            } catch (error) {
                                                console.log(err);
                                                throw error;
                                            }
                                        }
                                    }

                                    console.log("Writing data to file...");
                                    fs.writeFileSync(`./data/output-${province.rn}-${cityMun.rn}-${barangay.rn}-${precint.ppcc}.json`, JSON.stringify(output));
                                    x = x + 1;
                                    output = [];
                                }
                            }
                        }
                    }
                }
            }
        }
    }
})();
