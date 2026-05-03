// Server-side test for Letterman API integration
export default async function handler(req, res) {
  const LETTERMAN_API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI2OWE3OTI1YTQ3ODcyYjI4YjRjYTY2NTMiLCJrZXkiOiJiNDkwNjk2NDRlOTZjODg4YTAwNjhhZjhmZGRjMzViZSIsImlkIjoiNjlmNmI3ZTBhMTY2YWYyNjdlYzM5MzljIiwiaWF0IjoxNzc3Nzc2NjA4LCJleHAiOjE4MDkzMTI2MDh9.v83uVpQU6D7pnwpWvAnow2LHbRgg76nnmnBbw3rn2_I';
  
  const testResults = {
    timestamp: new Date().toISOString(),
    publication: 'Arlington Pulse',
    storageId: '69ee9d94a166af267eb5e972',
    tests: []
  };

  try {
    // Test 1: Fetch publication info
    const pubResponse = await fetch('https://api.letterman.ai/api/ai/newsletters-storage/69ee9d94a166af267eb5e972', {
      headers: { 'Authorization': `Bearer ${LETTERMAN_API_KEY}` }
    });
    
    const pubData = await pubResponse.json();
    testResults.tests.push({
      name: 'Publication Info',
      status: pubResponse.ok && !pubData.error ? 'PASS' : 'FAIL',
      data: {
        name: pubData.data?.name,
        domain: pubData.data?.domain,
        domainType: pubData.data?.domainType
      }
    });

    // Test 2: Fetch recent articles
    const articlesResponse = await fetch('https://api.letterman.ai/api/ai/newsletters-storage/69ee9d94a166af267eb5e972/newsletters?state=PUBLISHED&limit=5', {
      headers: { 'Authorization': `Bearer ${LETTERMAN_API_KEY}` }
    });
    
    const articlesData = await articlesResponse.json();
    
    if (articlesData.data && articlesData.data.length > 0) {
      const article = articlesData.data[0];
      testResults.tests.push({
        name: 'Article Fields',
        status: 'PASS',
        article: {
          title: article.title,
          slug: article.urlPath,
          excerpt: article.description,
          image: article.archiveThumbnailImageUrl || article.summary?.imageUrl,
          publishDate: article.createdAt,
          cityTag: article.term,
          state: article.state,
          contentPreview: article.content ? article.content.substring(0, 200) + '...' : 'No content'
        }
      });
    } else {
      testResults.tests.push({
        name: 'Article Fields',
        status: 'WARN',
        message: 'No published articles found'
      });
    }

    testResults.overall = testResults.tests.every(t => t.status !== 'FAIL') ? 'PASS' : 'PARTIAL';
    return res.status(200).json(testResults);

  } catch (error) {
    testResults.tests.push({
      name: 'API Connection',
      status: 'FAIL',
      error: error.message
    });
    testResults.overall = 'FAIL';
    return res.status(500).json(testResults);
  }
}
